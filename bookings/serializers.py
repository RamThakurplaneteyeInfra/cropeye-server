from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Booking, BookingComment, BookingAttachment
from users.serializers import IndustrySerializer
<<<<<<< HEAD
from users.models import Industry, Role
=======
from users.models import Industry
>>>>>>> 13a0b6b (Initial commit)

User = get_user_model()

# ---------------- User Serializer ----------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')


# ---------------- Booking Comment Serializer ----------------
class BookingCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BookingComment
        fields = ('id', 'user', 'content', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')


class BookingCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingComment
        fields = ('content',)


# ---------------- Booking Attachment Serializer ----------------
class BookingAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = BookingAttachment
        fields = ('id', 'file', 'uploaded_by', 'uploaded_at', 'description')
        read_only_fields = ('uploaded_at',)


class BookingAttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAttachment
        fields = ('file', 'description')


# ---------------- Booking Serializers ----------------

# GET / List / Retrieve
class BookingSerializer(serializers.ModelSerializer):
    # Frontend expects these exact names
    item_name = serializers.CharField(source="title", read_only=True)
<<<<<<< HEAD
    user_role = serializers.CharField(source="user_role.name", read_only=True)
    booking_type = serializers.CharField(read_only=True)
=======
    user_role = serializers.CharField(source="booking_type", read_only=True)
>>>>>>> 13a0b6b (Initial commit)

    created_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    industry = IndustrySerializer(read_only=True)
    comments = BookingCommentSerializer(many=True, read_only=True)
    attachments = BookingAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = (
            'id',
            'item_name',
            'user_role',
<<<<<<< HEAD
            'booking_type',
=======
>>>>>>> 13a0b6b (Initial commit)
            'start_date',
            'end_date',
            'status',
            'created_by',
            'approved_by',
            'industry',
            'created_at',
            'updated_at',
            'comments',
            'attachments',
        )
        read_only_fields = ('created_at', 'updated_at', 'approved_by', 'industry')


# POST / Create
class BookingCreateSerializer(serializers.ModelSerializer):
    # Make title optional (frontend sends item_name)
    item_name = serializers.CharField(source="title", required=False, allow_blank=True)
<<<<<<< HEAD
    # Accept user_role as role name (owner, manager, fieldofficer, farmer, vendor) and map to user_role ForeignKey
    user_role = serializers.CharField(write_only=True, required=True)
    booking_type = serializers.ChoiceField(choices=Booking.BOOKING_TYPES, required=False, allow_blank=True, allow_null=True)
=======
    user_role = serializers.ChoiceField(source="booking_type", choices=Booking.BOOKING_TYPES, required=True)
>>>>>>> 13a0b6b (Initial commit)

    # Optional industry assignment
    industry_id = serializers.PrimaryKeyRelatedField(
        source='industry',
        queryset=Industry.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Booking
        fields = (
            'item_name',
            'user_role',
<<<<<<< HEAD
            'booking_type',
=======
>>>>>>> 13a0b6b (Initial commit)
            'start_date',
            'end_date',
            'status',
            'industry_id',
        )

<<<<<<< HEAD
    def validate_user_role(self, value):
        """Validate that the role name exists"""
        valid_roles = ['owner', 'manager', 'fieldofficer', 'farmer', 'vendor']
        if value.lower() not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value.lower()

    def create(self, validated_data):
        """Create booking with role lookup"""
        role_name = validated_data.pop('user_role')
        try:
            role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            raise serializers.ValidationError(
                {'user_role': f'Role "{role_name}" does not exist in the system.'}
            )
        
        validated_data['user_role'] = role
        return super().create(validated_data)

=======
>>>>>>> 13a0b6b (Initial commit)

# PUT / PATCH
class BookingUpdateSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="title", required=False, allow_blank=True)
<<<<<<< HEAD
    # Accept user_role as role name (owner, manager, fieldofficer, farmer, vendor) and map to user_role ForeignKey
    user_role = serializers.CharField(write_only=True, required=False)
    booking_type = serializers.ChoiceField(choices=Booking.BOOKING_TYPES, required=False, allow_blank=True, allow_null=True)
=======
    user_role = serializers.ChoiceField(source="booking_type", choices=Booking.BOOKING_TYPES, required=False)
>>>>>>> 13a0b6b (Initial commit)

    class Meta:
        model = Booking
        fields = (
            'item_name',
            'user_role',
<<<<<<< HEAD
            'booking_type',
=======
>>>>>>> 13a0b6b (Initial commit)
            'start_date',
            'end_date',
            'status',
        )

<<<<<<< HEAD
    def validate_user_role(self, value):
        """Validate that the role name exists"""
        if value:
            valid_roles = ['owner', 'manager', 'fieldofficer', 'farmer', 'vendor']
            if value.lower() not in valid_roles:
                raise serializers.ValidationError(
                    f"Invalid role. Must be one of: {', '.join(valid_roles)}"
                )
            return value.lower()
        return value

    def update(self, instance, validated_data):
        """Update booking with role lookup if user_role is provided"""
        role_name = validated_data.pop('user_role', None)
        if role_name:
            try:
                role = Role.objects.get(name=role_name)
                validated_data['user_role'] = role
            except Role.DoesNotExist:
                raise serializers.ValidationError(
                    {'user_role': f'Role "{role_name}" does not exist in the system.'}
                )
        
        return super().update(instance, validated_data)


# PATCH Status only
class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('status',)

    def validate(self, attrs):
        if attrs['status'] not in ['approved', 'rejected', 'completed', 'cancelled', 'available', 'book', 'pending']:
            raise serializers.ValidationError({'status': 'Invalid status for this action.'})
        return attrs
