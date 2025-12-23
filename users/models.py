from django.contrib.auth.models import AbstractUser
from django.db import models
import re


class Industry(models.Model):
    """
    Industry model for multi-tenant isolation.
    Each industry has its own Industry Admin (Owner) and users.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    test_phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text="Test phone number for this industry (for testing purposes)"
    )
    test_password = models.CharField(
        max_length=128, 
        blank=True, 
        null=True,
        help_text="Test password for this industry (for testing purposes)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Role(models.Model):
    """
    A database-backed Role. You can assign any number of Django Permissions to it.
    """
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.display_name or self.name

class User(AbstractUser):
    # Username is required and used for login
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    
    # Temporary: reuse the old 'role' varchar column for the FK
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
        db_column='role',
    )

    # Multi-tenant: Industry association
    # Global Admin (is_superuser=True) can have industry=None to access all industries
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Industry this user belongs to. Null for Global Admin."
    )
    
    # Track who created this user (for manager -> field officer hierarchy)
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        help_text="Manager who created this user"
    )

    phone_number    = models.CharField(
        max_length=15, 
        unique=True,
        null=True,
        blank=True,
        help_text="Phone number (10 digits for India). Optional."
    )
    otp             = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at  = models.DateTimeField(null=True, blank=True)
    otp_delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('whatsapp', 'WhatsApp'),
            ('email', 'Email'),
        ],
        null=True,
        blank=True,
        help_text="Method used to deliver the last OTP"
    )
    
    # Password reset fields
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)
    address         = models.TextField(blank=True)
    village         = models.CharField(max_length=100, blank=True)
    state           = models.CharField(max_length=100, blank=True)
    district        = models.CharField(max_length=100, blank=True)
    taluka          = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use username as the USERNAME_FIELD (default)
    USERNAME_FIELD = 'username'
    # Update REQUIRED_FIELDS (phone_number is optional)
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        role = self.role.name if self.role else "NoRole"
        identifier = self.username or self.phone_number or self.email or "Unknown"
        return f"{identifier} ({role})"

    def has_role(self, role_name: str) -> bool:
        return bool(self.role and self.role.name == role_name)

    def has_any_role(self, role_names: list[str]) -> bool:
        return bool(self.role and self.role.name in role_names)
    
    def get_phone_number_with_country_code(self):
        """Get phone number formatted with +91 country code"""
        if self.phone_number:
            return f"+91{self.phone_number}"
        return None
    
    @property
    def phone_number_formatted(self):
        """Property to get phone number with +91 country code"""
        return self.get_phone_number_with_country_code()
    
    def clean(self):
        """Validate phone number format (10 digits for India) and handle +91 country code"""
        super().clean()
        # Convert empty string to None to avoid unique constraint issues
        if self.phone_number == '' or (isinstance(self.phone_number, str) and not self.phone_number.strip()):
            self.phone_number = None
        
        if self.phone_number:
            # Remove any non-digit characters
            cleaned_phone = re.sub(r'\D', '', self.phone_number)
            # If starts with 91 (country code), remove it to get 10 digits
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            # Check if it's exactly 10 digits
            if len(cleaned_phone) != 10:
                from django.core.exceptions import ValidationError
                raise ValidationError({'phone_number': 'Phone number must be exactly 10 digits (or 12 digits with +91).'})
            # Update phone_number to cleaned version
            self.phone_number = cleaned_phone
    
    def save(self, *args, **kwargs):
        # Convert empty string to None (NULL) to avoid unique constraint issues
        if self.phone_number == '' or (isinstance(self.phone_number, str) and not self.phone_number.strip()):
            self.phone_number = None
        
        # Clean phone number before saving
        if self.phone_number:
            cleaned_phone = re.sub(r'\D', '', self.phone_number)
            # If starts with 91 (country code), remove it to get 10 digits
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            self.phone_number = cleaned_phone
        self.full_clean()
        super().save(*args, **kwargs)

