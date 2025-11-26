from django.db import models
from django.conf import settings
from inventory.models import InventoryItem

# Indian States list for dropdown
INDIAN_STATES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
]

class Vendor(models.Model):
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    vendor_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(verbose_name="Email ID")
    phone = models.CharField(max_length=20, verbose_name="Mobile Number")
    gstin_number = models.CharField(max_length=15, blank=True, null=True, verbose_name="GSTIN Number", help_text="15-digit GSTIN number")
    state = models.CharField(max_length=100, choices=INDIAN_STATES, blank=True, null=True, verbose_name="State")
    city = models.CharField(max_length=100, blank=True, verbose_name="City")
    address = models.TextField()
    website = models.URLField(blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['vendor_name']
        indexes = [
            models.Index(fields=['vendor_name']),
            models.Index(fields=['rating']),
            models.Index(fields=['gstin_number']),
        ]
    
    def __str__(self):
        return self.vendor_name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    order_number = models.CharField(max_length=50, unique=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Invoice Number")
    invoice_date = models.DateField(null=True, blank=True, verbose_name="Invoice Date")
    state = models.CharField(max_length=100, choices=INDIAN_STATES, blank=True, null=True, verbose_name="State")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_purchase_orders')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    issue_date = models.DateField()
    expected_delivery_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issue_date']),
            models.Index(fields=['expected_delivery_date']),
        ]
    
    def __str__(self):
        return f"PO-{self.order_number} ({self.vendor.vendor_name})"
    
    def calculate_total(self):
        """Calculate the total amount of the purchase order"""
        total = sum(item.total_price for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='purchase_order_items', null=True, blank=True)
    item_name = models.CharField(max_length=200, blank=True, verbose_name="Item Name", help_text="Item name if not from inventory")
    year_of_make = models.CharField(max_length=10, blank=True, null=True, verbose_name="YearOfMake")
    estimate_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="EstimateCost")
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    remark = models.TextField(blank=True, verbose_name="Remark")
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['item_name', 'inventory_item__item_name']
    
    def __str__(self):
        item_display = self.item_name or (self.inventory_item.item_name if self.inventory_item else "Unknown")
        return f"{item_display} - {self.quantity if self.quantity else 'N/A'} units"
    
    def save(self, *args, **kwargs):
        # Calculate total price - use estimate_cost if available, otherwise quantity * unit_price
        if self.estimate_cost:
            self.total_price = self.estimate_cost
        elif self.unit_price and self.quantity:
            self.total_price = self.quantity * self.unit_price
        else:
            self.total_price = 0
        
        super().save(*args, **kwargs)
        
        # Update the purchase order total
        self.purchase_order.calculate_total()

class Order(models.Model):
    """
    Order model for Accounting - matches the screenshot requirements
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='orders', verbose_name="Vendor Name")
    invoice_number = models.CharField(max_length=100, verbose_name="Invoice Number")
    invoice_date = models.DateField(verbose_name="Invoice Date")
    state = models.CharField(max_length=100, choices=INDIAN_STATES, verbose_name="State")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date', '-created_at']
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['invoice_date']),
            models.Index(fields=['state']),
        ]
    
    def __str__(self):
        return f"Order - {self.invoice_number} ({self.vendor.vendor_name})"

class OrderItem(models.Model):
    """
    OrderItem model for Manage Items section - matches the screenshot requirements
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200, verbose_name="Item Name")
    year_of_make = models.CharField(max_length=10, blank=True, null=True, verbose_name="YearOfMake")
    estimate_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="EstimateCost")
    remark = models.TextField(blank=True, verbose_name="Remark")
    
    class Meta:
        ordering = ['item_name']
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
    
    def __str__(self):
        return f"{self.item_name} - {self.order.invoice_number}"

class VendorCommunication(models.Model):
    COMMUNICATION_TYPES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='communications')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    date = models.DateTimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.get_communication_type_display()} with {self.vendor.vendor_name} on {self.date}"
