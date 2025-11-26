from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class PhoneNumberBackend(ModelBackend):
    """
    Custom authentication backend that authenticates users using phone_number instead of username.
    """
    
    def authenticate(self, request, phone_number=None, password=None, **kwargs):
        """
        Authenticate a user using phone_number and password.
        """
        if phone_number is None or password is None:
            return None
        
        # Clean phone number (remove non-digit characters)
        cleaned_phone = re.sub(r'\D', '', phone_number)
        
        # If starts with 91 (country code), remove it to get 10 digits
        if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
            cleaned_phone = cleaned_phone[2:]
        
        if len(cleaned_phone) != 10:
            return None
        
        try:
            user = User.objects.get(phone_number=cleaned_phone)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by ID.
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None

