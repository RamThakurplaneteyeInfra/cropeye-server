from rest_framework import serializers
from .models import InventoryItem, InventoryTransaction, Stock
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class InventoryItemSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    industry = serializers.PrimaryKeyRelatedField(read_only=True)
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = [
            'id', 'item_name', 'description', 'quantity', 'unit', 
            'purchase_date', 'expiry_date', 'category', 'status', 
            'reorder_level', 'industry', 'industry_name', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'industry']
    
    def create(self, validated_data):
        # created_by and industry are set in perform_create() in the viewset
        return super().create(validated_data)

class InventoryTransactionSerializer(serializers.ModelSerializer):
    performed_by = UserSerializer(read_only=True)
    inventory_item_name = serializers.CharField(source='inventory_item.item_name', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'inventory_item', 'inventory_item_name', 'transaction_type', 
            'quantity', 'transaction_date', 'performed_by', 'notes'
        ]
        read_only_fields = ['transaction_date']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['performed_by'] = user
        return super().create(validated_data)

class InventoryItemDetailSerializer(InventoryItemSerializer):
    transactions = InventoryTransactionSerializer(many=True, read_only=True)
    
    class Meta(InventoryItemSerializer.Meta):
        fields = InventoryItemSerializer.Meta.fields + ['transactions']

class StockSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    industry = serializers.PrimaryKeyRelatedField(read_only=True)
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'item_name', 'item_type', 'item_type_display', 'make', 
            'year_of_make', 'estimate_cost', 'status', 'status_display', 
            'industry', 'industry_name', 'remark', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'industry']
    
    def _normalize_item_type(self, value):
        """Normalize item_type to accept both display names and keys (case-insensitive)"""
        if not value:
            return value
        
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        # Map of display names (lowercase) to keys
        display_to_key = {
            'logistic': 'logistic',
            'transport': 'transport',
            'equipment': 'equipment',
            'office purpose': 'office_purpose',
            'officepurpose': 'office_purpose',
            'storage': 'storage',
            'processing': 'processing',
        }
        
        # Check if it's already a valid key (case-insensitive)
        if value_lower in display_to_key:
            return display_to_key[value_lower]
        
        # Check if it matches a display name (case-insensitive)
        for key, display in Stock.ITEM_TYPE_CHOICES:
            if display.lower() == value_lower or key.lower() == value_lower:
                return key
        
        # If no match, return original (will be validated by Django)
        return value_str
    
    def _normalize_status(self, value):
        """Normalize status to accept both display names and keys (case-insensitive)"""
        if not value:
            return value
        
        value_str = str(value).strip()
        value_lower = value_str.lower()
        
        # Map common variations
        variations = {
            'not working': 'not_working',
            'not-working': 'not_working',
            'notworking': 'not_working',
            'underrepair': 'under_repair',  # Frontend sends 'underRepair' (lowercased)
            'under repair': 'under_repair',
            'under-repair': 'under_repair',
        }
        
        # Check variations first
        if value_lower in variations:
            return variations[value_lower]
        
        # Check if it's already a valid key (case-insensitive)
        valid_keys = [choice[0] for choice in Stock.STATUS_CHOICES]
        if value_lower in valid_keys:
            return value_lower
        
        # Check if it matches a display name (case-insensitive)
        for key, display in Stock.STATUS_CHOICES:
            if display.lower() == value_lower or key.lower() == value_lower:
                return key
        
        # If no match, return original (will be validated by Django)
        return value_str
    
    def validate_item_type(self, value):
        """Validate and normalize item_type"""
        normalized = self._normalize_item_type(value)
        # Validate that the normalized value is a valid choice
        valid_keys = [choice[0] for choice in Stock.ITEM_TYPE_CHOICES]
        if normalized not in valid_keys:
            valid_choices = ', '.join([f'"{c[0]}" or "{c[1]}"' for c in Stock.ITEM_TYPE_CHOICES])
            raise serializers.ValidationError(
                f'Invalid item_type. Valid choices are: {valid_choices}'
            )
        return normalized
    
    def validate_status(self, value):
        """Validate and normalize status"""
        normalized = self._normalize_status(value)
        # Validate that the normalized value is a valid choice
        valid_keys = [choice[0] for choice in Stock.STATUS_CHOICES]
        if normalized not in valid_keys:
            valid_choices = ', '.join([f'"{c[0]}" or "{c[1]}"' for c in Stock.STATUS_CHOICES])
            raise serializers.ValidationError(
                f'Invalid status. Valid choices are: {valid_choices}'
            )
        return normalized
    
    def create(self, validated_data):
        # created_by and industry are set in perform_create() in the viewset
        return super().create(validated_data) 