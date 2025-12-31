from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderItem, VendorCommunication, Order, OrderItem
from inventory.serializers import InventoryItemSerializer
from django.contrib.auth import get_user_model
from users.models import Industry

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class VendorSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    industry = serializers.PrimaryKeyRelatedField(
        queryset=Industry.objects.all(),
        required=False,
        allow_null=True
    )
    industry_name = serializers.CharField(source='industry.name', read_only=True)

    gstin_number = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="15-digit GSTIN number"
    )

    class Meta:
        model = Vendor
        fields = [
            'id', 'vendor_name', 'contact_person', 'email', 'phone',
            'gstin_number', 'state', 'city', 'address', 'website', 'rating', 'notes',
            'industry', 'industry_name', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user:
            user_industry = getattr(request.user, 'industry', None)
            if request.user.is_superuser:
                self.fields['industry'].queryset = Industry.objects.all()
            elif user_industry:
                self.fields['industry'].queryset = Industry.objects.filter(id=user_industry.id)
            else:
                self.fields['industry'].queryset = Industry.objects.none()

    def validate_gstin_number(self, value):
        if value is None:
            return None
        value = str(value).strip() if value else ''
        if not value:
            return None
        value = value.upper()
        instance = getattr(self, 'instance', None)
        if instance:
            existing = Vendor.objects.filter(gstin_number=value).exclude(pk=instance.pk).first()
        else:
            existing = Vendor.objects.filter(gstin_number=value).first()
        if existing:
            raise serializers.ValidationError(f"A vendor with GSTIN number '{value}' already exists.")
        return value

    def create(self, validated_data):
        return super().create(validated_data)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    inventory_item_name = serializers.CharField(source='inventory_item.item_name', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'inventory_item', 'inventory_item_name',
            'quantity', 'unit_price', 'total_price', 'notes'
        ]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    vendor_name = serializers.CharField(source='vendor.vendor_name', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'vendor', 'vendor_name', 'order_number', 'status',
            'created_by', 'approved_by', 'issue_date', 'expected_delivery_date',
            'delivery_date', 'notes', 'total_amount', 'items',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class VendorCommunicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    vendor_name = serializers.CharField(source='vendor.vendor_name', read_only=True)
    purchase_order_number = serializers.CharField(source='purchase_order.order_number', read_only=True)

    class Meta:
        model = VendorCommunication
        fields = [
            'id', 'vendor', 'vendor_name', 'purchase_order', 'purchase_order_number',
            'communication_type', 'subject', 'message', 'date',
            'user', 'created_at'
        ]
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class VendorDetailSerializer(VendorSerializer):
    purchase_orders = PurchaseOrderSerializer(many=True, read_only=True)
    communications = VendorCommunicationSerializer(many=True, read_only=True)

    class Meta(VendorSerializer.Meta):
        fields = VendorSerializer.Meta.fields + ['purchase_orders', 'communications']


class PurchaseOrderDetailSerializer(PurchaseOrderSerializer):
    communications = VendorCommunicationSerializer(many=True, read_only=True)

    class Meta(PurchaseOrderSerializer.Meta):
        fields = PurchaseOrderSerializer.Meta.fields + ['communications']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item_name', 'year_of_make', 'estimate_cost', 'remark']


class OrderSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    vendor_name = serializers.CharField(source='vendor.vendor_name', read_only=True)
    industry = serializers.PrimaryKeyRelatedField(read_only=True)
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'vendor', 'vendor_name', 'invoice_number', 'invoice_date',
            'state', 'industry', 'industry_name', 'created_by', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'industry']

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        if hasattr(user, 'industry') and user.industry:
            validated_data['industry'] = user.industry
        return super().create(validated_data)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = ['vendor', 'invoice_number', 'invoice_date', 'state', 'items']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None
        user_industry = getattr(user, 'industry', None) if user else None

        items_data = validated_data.pop('items', [])

        # Create order without items first
        order_data = validated_data.copy()
        if user:
            order_data['created_by'] = user
        if user_industry:
            order_data['industry'] = user_industry

        order = Order.objects.create(**order_data)

        # Create items and link them to the order
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order


class OrderDetailSerializer(OrderSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields
