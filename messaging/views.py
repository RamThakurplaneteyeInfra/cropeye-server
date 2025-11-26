from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Max
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Message, Conversation
from .serializers import (
    MessageSerializer, 
    ConversationSerializer, 
    CreateMessageSerializer,
    UserBasicSerializer
)
from .permissions import CanCommunicateWith

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated, CanCommunicateWith]
    
    def get_queryset(self):
        """Get conversations for the current user"""
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user)
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time', '-updated_at')
    
    @action(detail=False, methods=['get'], url_path='with-user/(?P<user_id>[^/.]+)')
    def with_user(self, request, user_id=None):
        """Get or create conversation with a specific user"""
        try:
            recipient = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if users can communicate
        if not CanCommunicateWith.can_communicate(request.user, recipient):
            return Response(
                {"error": "You do not have permission to communicate with this user."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create conversation
        conversation, created = Conversation.get_or_create_conversation(
            request.user, 
            recipient
        )
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """Get all messages in a conversation"""
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark all messages in conversation as read"""
        conversation = self.get_object()
        user = request.user
        
        # Mark all unread messages from other participant as read
        unread_messages = conversation.messages.filter(
            sender=conversation.get_other_participant(user),
            read_at__isnull=True
        )
        
        count = unread_messages.update(read_at=timezone.now())
        return Response({
            "message": f"Marked {count} message(s) as read.",
            "count": count
        })


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, CanCommunicateWith]
    
    def get_queryset(self):
        """Get messages for the current user"""
        user = self.request.user
        return Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user)
        ).select_related('sender', 'conversation')
    
    def create(self, request, *args, **kwargs):
        """Create a new message - supports single or multiple recipients"""
        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        recipient_ids = serializer.validated_data['recipient_id']
        content = serializer.validated_data['content']
        
        # Ensure recipient_ids is always a list for consistent processing
        if not isinstance(recipient_ids, list):
            recipient_ids = [recipient_ids]
        
        created_messages = []
        errors = []
        
        for recipient_id in recipient_ids:
            try:
                recipient = User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                errors.append({
                    "recipient_id": recipient_id,
                    "error": "Recipient user not found."
                })
                continue
            
            # Check if users can communicate
            if not CanCommunicateWith.can_communicate(request.user, recipient):
                errors.append({
                    "recipient_id": recipient_id,
                    "error": "You do not have permission to communicate with this user."
                })
                continue
            
            # Get or create conversation
            conversation, created = Conversation.get_or_create_conversation(
                request.user, 
                recipient
            )
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            
            # Update conversation's last_message_at
            conversation.last_message_at = message.created_at
            conversation.save(update_fields=['last_message_at'])
            
            message_serializer = MessageSerializer(message, context={'request': request})
            created_messages.append(message_serializer.data)
        
        # Return response
        if errors and not created_messages:
            # All failed
            return Response({
                "error": "Failed to send messages to all recipients.",
                "errors": errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if errors:
            # Partial success
            return Response({
                "messages_sent": len(created_messages),
                "messages_failed": len(errors),
                "created_messages": created_messages,
                "errors": errors
            }, status=status.HTTP_207_MULTI_STATUS)
        
        # If only one message, return single message format (backward compatibility)
        if len(created_messages) == 1:
            return Response(created_messages[0], status=status.HTTP_201_CREATED)
        
        # Multiple messages sent successfully
        return Response({
            "messages_sent": len(created_messages),
            "messages": created_messages
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = self.get_object()
        
        # Only recipient can mark as read
        if message.sender == request.user:
            return Response(
                {"error": "You cannot mark your own message as read."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if message.conversation.participant1 != request.user and message.conversation.participant2 != request.user:
            return Response(
                {"error": "You do not have permission to mark this message as read."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.mark_as_read()
        return Response({"message": "Message marked as read."})
    
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get total unread message count for current user"""
        user = request.user
        count = Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user)
        ).exclude(
            sender=user
        ).filter(
            read_at__isnull=True
        ).count()
        
        return Response({"unread_count": count})
    
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        """Get all unread messages for current user"""
        user = request.user
        unread_messages = Message.objects.filter(
            Q(conversation__participant1=user) | Q(conversation__participant2=user)
        ).exclude(
            sender=user
        ).filter(
            read_at__isnull=True
        ).select_related('sender', 'conversation').order_by('-created_at')
        
        serializer = self.get_serializer(unread_messages, many=True)
        return Response(serializer.data)
