from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone

class Booking(models.Model):
    BOOKING_TYPES = [
        ('meeting', 'Meeting'),
        ('field', 'Field Work'),
        ('maintenance', 'Maintenance'),
        ('training', 'Training'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('book', 'Book'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    industry = models.ForeignKey(
        'users.Industry',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='bookings',
        help_text="Industry this booking belongs to"
    )
    
    title = models.CharField(max_length=200, blank=True, null=True)  # <-- Made optional
    item_name = models.CharField(max_length=200, blank=True, verbose_name="Item Name", help_text="Name of the item being booked")
    description = models.TextField(blank=True)
    booking_type = models.CharField(max_length=20, choices=BOOKING_TYPES, blank=True, null=True)
    user_role = models.ForeignKey(
        'users.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name="User Role",
        help_text="Role assigned to this booking"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_bookings')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bookings')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['booking_type']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]

    def __str__(self):
        display_name = self.item_name or self.title or "No Title"
        return f"{display_name} - {self.get_status_display()}"

    def clean(self):
        # Validate that end_date is after start_date
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError('End date must be after start date')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class BookingComment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.booking.title or 'No Title'}"


class BookingAttachment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='booking_attachments/')
    description = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.booking.title or 'No Title'}"