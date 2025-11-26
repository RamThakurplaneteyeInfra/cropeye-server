from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Message, Conversation

User = get_user_model()


class RecipientIdField(serializers.Field):
    """
    Custom field that accepts both a single integer or a list of integers
    for recipient_id in messages
    """
    
    def to_internal_value(self, data):
        """Convert incoming data to internal value"""
        # Accept both int and list
        if isinstance(data, list):
            return data
        elif isinstance(data, (int, str)):
            # Convert string to int if needed
            try:
                return int(data)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Invalid recipient_id: {data}. Must be a valid integer."
                )
        else:
            raise serializers.ValidationError(
                "recipient_id must be an integer or a list of integers."
            )
    
    def to_representation(self, value):
        """Convert internal value to representation"""
        return value


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user serializer for message participants"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display = serializers.CharField(source='role.display_name', read_only=True)
    phone_number_formatted = serializers.SerializerMethodField(read_only=True)
    
    def get_phone_number_formatted(self, obj):
        """Get formatted phone number with country code"""
        return obj.phone_number_formatted if hasattr(obj, 'phone_number_formatted') else None
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 
                  'phone_number', 'phone_number_formatted', 'role_name', 'role_display', 'profile_picture']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'email', 
                           'phone_number', 'phone_number_formatted', 'role_name', 'role_display', 'profile_picture']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model"""
    sender = UserBasicSerializer(read_only=True)
    is_read = serializers.BooleanField(read_only=True)
    conversation_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = ['id', 'conversation', 'conversation_id', 'sender', 'content', 
                  'read_at', 'is_read', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sender', 'read_at', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new message"""
        conversation_id = validated_data.pop('conversation_id', None)
        if conversation_id:
            from .models import Conversation
            validated_data['conversation'] = Conversation.objects.get(id=conversation_id)
        
        # Set sender from request user
        validated_data['sender'] = self.context['request'].user
        
        # Update conversation's last_message_at
        message = Message.objects.create(**validated_data)
        message.conversation.last_message_at = message.created_at
        message.conversation.save(update_fields=['last_message_at'])
        
        return message


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for Conversation model"""
    participant1 = UserBasicSerializer(read_only=True)
    participant2 = UserBasicSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participant1', 'participant2', 'other_participant',
                  'last_message', 'unread_count', 'created_at', 'updated_at', 
                  'last_message_at']
        read_only_fields = ['id', 'participant1', 'participant2', 'created_at', 
                           'updated_at', 'last_message_at']
    
    def get_last_message(self, obj):
        """Get the last message in the conversation"""
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user"""
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0
    
    def get_other_participant(self, obj):
        """Get the other participant (not the current user)"""
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            return UserBasicSerializer(other).data
        return None


class CreateMessageSerializer(serializers.Serializer):
    """Serializer for creating a new message - supports single or multiple recipients"""
    recipient_id = RecipientIdField(required=True)  # Accepts both int and list
    content = serializers.CharField(required=True, max_length=5000)
    
    def validate_recipient_id(self, value):
        """Validate recipient(s) exist - accepts single ID or list of IDs"""
        # Handle array of recipient IDs
        if isinstance(value, list):
            if not value:
                raise serializers.ValidationError("recipient_id list cannot be empty.")
            
            # Validate all recipients exist and convert to integers
            recipient_ids = []
            for recipient_id in value:
                try:
                    recipient_id_int = int(recipient_id)
                    recipient_ids.append(recipient_id_int)
                except (ValueError, TypeError):
                    raise serializers.ValidationError(
                        f"Invalid recipient_id in list: {recipient_id}. Must be a valid integer."
                    )
                
                try:
                    User.objects.get(id=recipient_id_int)
                except User.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Recipient user with ID {recipient_id_int} does not exist."
                    )
            
            return recipient_ids
        
        # Handle single recipient ID (backward compatibility)
        elif isinstance(value, (int, str)):
            try:
                recipient_id = int(value)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    f"Invalid recipient_id: {value}. Must be a valid integer."
                )
            
            try:
                User.objects.get(id=recipient_id)
            except User.DoesNotExist:
                raise serializers.ValidationError(f"Recipient user with ID {recipient_id} does not exist.")
            
            return recipient_id
        
        else:
            raise serializers.ValidationError(
                "recipient_id must be an integer or a list of integers."
            )
