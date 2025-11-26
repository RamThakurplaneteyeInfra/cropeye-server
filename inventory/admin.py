from django.contrib import admin
from .models import InventoryItem, InventoryTransaction, Stock

class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 1
    readonly_fields = ['transaction_date']

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'industry', 'quantity', 'unit', 'category', 'status', 'purchase_date', 'expiry_date')
    list_filter = ('industry', 'status', 'category')
    search_fields = ('item_name', 'description', 'industry__name')
    readonly_fields = ('status', 'created_at', 'updated_at')
    inlines = [InventoryTransactionInline]
    fieldsets = (
        (None, {'fields': ('item_name', 'description', 'industry', 'quantity', 'unit')}),
        ('Classification', {'fields': ('category', 'status')}),
        ('Dates', {'fields': ('purchase_date', 'expiry_date')}),
        ('Thresholds', {'fields': ('reorder_level',)}),
        ('Metadata', {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'transaction_type', 'quantity', 'transaction_date', 'performed_by')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('inventory_item__item_name', 'notes')
    readonly_fields = ('transaction_date',)
    date_hierarchy = 'transaction_date'

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """
    Stock Admin - matches the "Add New Stock" form in screenshot
    Fields: Item Name, Item Type, Make, Year of Make, Estimate Cost, Status, Remark
    """
    list_display = ('item_name', 'item_type', 'make', 'year_of_make', 'status', 'estimate_cost', 'created_at')
    list_filter = ('item_type', 'status', 'created_at')
    search_fields = ('item_name', 'make', 'remark')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': (
                ('item_name', 'item_type'),
                ('make', 'year_of_make'),
                ('estimate_cost', 'status'),
            ),
            'description': 'Enter the stock details. All fields are optional except Item Name.'
        }),
        ('Additional Information', {
            'fields': ('remark',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default created_by to current user for new stocks
        if not obj:
            form.base_fields['created_by'].initial = request.user
            form.base_fields['created_by'].required = False
        return form
    
    def save_model(self, request, obj, form, change):
        # Set created_by automatically for new stocks
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
