from django.db import models
from django.conf import settings
from django.utils import timezone

class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('seeds', 'Seeds'),
        ('fertilizers', 'Fertilizers'),
        ('pesticides', 'Pesticides'),
        ('tools', 'Tools'),
        ('equipment', 'Equipment'),
        ('feed', 'Animal Feed'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('expired', 'Expired'),
    ]
    
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50)
    purchase_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_stock')
    reorder_level = models.IntegerField(default=0, help_text="Minimum quantity before reorder is needed")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['item_name']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit}"
    
    def save(self, *args, **kwargs):
        # Automatically update status based on quantity
        if self.quantity <= 0:
            self.status = 'out_of_stock'
        elif self.quantity <= self.reorder_level:
            self.status = 'low_stock'
        else:
            self.status = 'in_stock'
            
        # Check expiry date
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.status = 'expired'
            
        super().save(*args, **kwargs)

class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('addition', 'Addition'),
        ('removal', 'Removal'),
        ('adjustment', 'Adjustment'),
    ]
    
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    transaction_date = models.DateTimeField(auto_now_add=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} of {self.quantity} {self.inventory_item.unit} to {self.inventory_item.item_name}"
    
    def save(self, *args, **kwargs):
        # Update the inventory quantity based on transaction type
        if self.transaction_type == 'addition':
            self.inventory_item.quantity += self.quantity
        elif self.transaction_type == 'removal':
            self.inventory_item.quantity -= self.quantity
        elif self.transaction_type == 'adjustment':
            # For adjustment, the quantity represents the new total
            self.inventory_item.quantity = self.quantity
        
        # Save the inventory item to update its quantity and status
        self.inventory_item.save()
        
        super().save(*args, **kwargs)
