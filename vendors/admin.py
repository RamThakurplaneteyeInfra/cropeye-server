from django.contrib import admin
from django import forms
from .models import Vendor, PurchaseOrder, PurchaseOrderItem, VendorCommunication, Order, OrderItem, INDIAN_STATES

class PurchaseOrderInline(admin.TabularInline):
    model = PurchaseOrder
    extra = 0
    fields = ['order_number', 'status', 'issue_date', 'expected_delivery_date', 'total_amount']
    readonly_fields = ['total_amount']
    show_change_link = True

class VendorCommunicationInline(admin.TabularInline):
    model = VendorCommunication
    extra = 0
    fields = ['communication_type', 'subject', 'date', 'user']
    readonly_fields = ['date', 'user']
    show_change_link = True

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('vendor_name', 'industry', 'contact_person', 'email', 'phone', 'city', 'state', 'rating')
    list_filter = ('industry', 'rating', 'state', 'city')
    search_fields = ('vendor_name', 'contact_person', 'email', 'phone', 'gstin_number', 'city', 'industry__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PurchaseOrderInline, VendorCommunicationInline]
    
    fieldsets = (
        ('Vendor Information', {
            'fields': ('vendor_name', 'contact_person', 'email', 'phone', 'gstin_number')
        }),
        ('Location', {
            'fields': ('state', 'city', 'address')
        }),
        ('Additional Information', {
            'fields': ('website', 'rating', 'notes'),
            'classes': ('collapse',)
        }),
        ('Industry & Metadata', {
            'fields': ('industry', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superuser sees everything
        if request.user.is_superuser:
            return qs
        # Filter by user's industry
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        # Return empty queryset if user has no industry
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default created_by to current user for new vendors
        if not obj:  # Creating new vendor
            form.base_fields['created_by'].initial = request.user
            form.base_fields['created_by'].required = False
        return form
    
    def save_model(self, request, obj, form, change):
        # Set created_by automatically for new vendors
        if not change:  # New vendor
            obj.created_by = request.user
            # Set industry from user if not set
            if not obj.industry:
                if hasattr(request.user, 'industry') and request.user.industry:
                    obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['item_name', 'inventory_item', 'year_of_make', 'estimate_cost', 'remark']
    verbose_name = "Item"
    verbose_name_plural = "Manage Items"
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Make inventory_item optional
        formset.form.base_fields['inventory_item'].required = False
        formset.form.base_fields['item_name'].required = False
        return formset

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'invoice_number', 'vendor', 'invoice_date', 'status', 'total_amount')
    list_filter = ('status', 'invoice_date', 'issue_date')
    search_fields = ('order_number', 'invoice_number', 'vendor__vendor_name', 'notes')
    readonly_fields = ('total_amount', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]
    
    fieldsets = (
        ('Vendor & Invoice Information', {
            'fields': ('vendor', 'invoice_date', 'invoice_number', 'state')
        }),
        ('Order Details', {
            'fields': ('order_number', 'status', 'issue_date', 'expected_delivery_date', 'delivery_date')
        }),
        ('Financial', {
            'fields': ('total_amount', 'notes')
        }),
        ('Approval', {
            'fields': ('created_by', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set initial state from vendor if creating new order and vendor is selected
        if not obj and 'vendor' in form.base_fields:
            # This will be set via JavaScript or form handling
            pass
        
        # Set default created_by to current user for new orders
        if not obj:
            form.base_fields['created_by'].initial = request.user
            form.base_fields['created_by'].required = False
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'purchase_order', 'quantity', 'unit_price', 'total_price')
    list_filter = ('purchase_order__status',)
    search_fields = ('inventory_item__item_name', 'purchase_order__order_number', 'notes')
    readonly_fields = ['total_price']
    
class OrderItemInline(admin.TabularInline):
    """
    Inline admin for Order Items - matches the "Manage Items" section in screenshot
    """
    model = OrderItem
    extra = 1
    fields = ['item_name', 'year_of_make', 'estimate_cost', 'remark']
    verbose_name = "Item"
    verbose_name_plural = "Manage Items"
    can_delete = True

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Order Admin - matches the Accounting form in screenshot
    Fields: Vendor Name, Invoice Number, Invoice Date, State
    """
    list_display = ('invoice_number', 'vendor', 'industry', 'invoice_date', 'state', 'created_at')
    list_filter = ('industry', 'state', 'invoice_date', 'created_at')
    search_fields = ('invoice_number', 'vendor__vendor_name', 'industry__name')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('vendor', 'invoice_number', 'invoice_date', 'state'),
            'description': 'Enter the order details. All fields marked with * are required.'
        }),
        ('Industry & Metadata', {
            'fields': ('industry', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superuser sees everything
        if request.user.is_superuser:
            return qs
        # Filter by user's industry
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        # Return empty queryset if user has no industry
        return qs.none()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default created_by to current user for new orders
        if not obj:
            form.base_fields['created_by'].initial = request.user
            form.base_fields['created_by'].required = False
        return form
    
    def save_model(self, request, obj, form, change):
        # Set created_by automatically for new orders
        if not change:
            obj.created_by = request.user
            # Set industry from user if not set
            if not obj.industry:
                if hasattr(request.user, 'industry') and request.user.industry:
                    obj.industry = request.user.industry
        super().save_model(request, obj, form, change)
    

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'order', 'year_of_make', 'estimate_cost')
    list_filter = ('order__invoice_date',)
    search_fields = ('item_name', 'order__invoice_number', 'remark')
    raw_id_fields = ('order',)

@admin.register(VendorCommunication)
class VendorCommunicationAdmin(admin.ModelAdmin):
    list_display = ('subject', 'vendor', 'communication_type', 'date', 'user')
    list_filter = ('communication_type', 'date')
    search_fields = ('subject', 'message', 'vendor__vendor_name')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {'fields': ('vendor', 'purchase_order', 'communication_type')}),
        ('Message', {'fields': ('subject', 'message', 'date')}),
        ('Metadata', {'fields': ('user', 'created_at'), 'classes': ('collapse',)}),
    )
