from rest_framework import permissions
from django.core.exceptions import PermissionDenied


class CanCommunicateWith(permissions.BasePermission):
    """
    Permission class to check if a user can communicate with another user
    based on the role hierarchy.
    
    Communication Rules:
    - Owner ↔ Manager (bidirectional)
    - Manager ↔ Field Officer (bidirectional)
    - Field Officer ↔ Manager ↔ Owner (Field Officer can message both)
    - Field Officer ↔ Farmer (bidirectional)
    - Farmer ↔ Field Officer (bidirectional)
    """
    
    @staticmethod
    def can_communicate(user1, user2):
        """
        Check if user1 can communicate with user2
        """
        # Same user cannot message themselves
        if user1 == user2:
            return False
        
        # Get roles
        role1 = user1.role.name if user1.role else None
        role2 = user2.role.name if user2.role else None
        
        # Superuser and admin can communicate with anyone
        if user1.is_superuser or (role1 == 'admin'):
            return True
        
        # If either user has no role, deny
        if not role1 or not role2:
            return False
        
        # Owner ↔ Manager (bidirectional)
        if (role1 == 'owner' and role2 == 'manager') or (role1 == 'manager' and role2 == 'owner'):
            return True
        
        # Manager ↔ Field Officer (bidirectional)
        if (role1 == 'manager' and role2 == 'fieldofficer') or (role1 == 'fieldofficer' and role2 == 'manager'):
            return True
        
        # Field Officer ↔ Owner (Field Officer can message Owner)
        if role1 == 'fieldofficer' and role2 == 'owner':
            return True
        
        # Owner can message Field Officer (through manager hierarchy)
        if role1 == 'owner' and role2 == 'fieldofficer':
            return True
        
        # Field Officer ↔ Farmer (bidirectional)
        if (role1 == 'fieldofficer' and role2 == 'farmer') or (role1 == 'farmer' and role2 == 'fieldofficer'):
            return True
        
        # Manager ↔ Farmer (Manager can message farmers through field officers)
        if (role1 == 'manager' and role2 == 'farmer') or (role1 == 'farmer' and role2 == 'manager'):
            return True
        
        # Owner ↔ Farmer (Owner can message farmers through hierarchy)
        if (role1 == 'owner' and role2 == 'farmer') or (role1 == 'farmer' and role2 == 'owner'):
            return True
        
        return False
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow list/create actions - permission will be checked in the view
        if view.action in ['list', 'create', 'conversations', 'unread_count']:
            return True
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access a specific object"""
        user = request.user
        
        if isinstance(obj, Message):
            # User can access message if they are sender or receiver
            if obj.sender == user:
                return True
            if obj.conversation.participant1 == user or obj.conversation.participant2 == user:
                return True
            return False
        
        if isinstance(obj, Conversation):
            # User can access conversation if they are a participant
            return obj.participant1 == user or obj.participant2 == user
        
        return False

