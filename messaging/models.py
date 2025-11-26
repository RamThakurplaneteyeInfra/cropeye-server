from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """
    Represents a conversation between two users.
    Automatically creates a unique conversation for each pair of users.
    """
    participant1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant1'
    )
    participant2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant2'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['participant1', 'participant2']
        ordering = ['-last_message_at', '-updated_at']
        indexes = [
            models.Index(fields=['participant1', 'participant2']),
            models.Index(fields=['-last_message_at']),
        ]
    
    def __str__(self):
        return f"Conversation: {self.participant1.username} ↔ {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_unread_count(self, user):
        """Get unread message count for a user"""
        return self.messages.filter(
            sender=self.get_other_participant(user),
            read_at__isnull=True
        ).count()
    
    @classmethod
    def get_or_create_conversation(cls, user1, user2):
        """Get or create a conversation between two users"""
        # Ensure consistent ordering (smaller ID first)
        if user1.id > user2.id:
            user1, user2 = user2, user1
        
        conversation, created = cls.objects.get_or_create(
            participant1=user1,
            participant2=user2
        )
        return conversation, created


class Message(models.Model):
    """
    Represents a message in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
    
    @property
    def is_read(self):
        """Check if message is read"""
        return self.read_at is not None

