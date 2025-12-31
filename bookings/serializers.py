from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Booking, BookingComment, BookingAttachment
from users.serializers import IndustrySerializer
from users.models import Industry

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
    user_role = serializers.CharField(source="booking_type", read_only=True)

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
    # Frontend fields
    item_name = serializers.CharField(source="title", required=True)
    user_role = serializers.ChoiceField(source="booking_type", choices=Booking.BOOKING_TYPES, required=True)

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
            'start_date',
            'end_date',
            'status',
            'industry_id',
        )


# PUT / PATCH
class BookingUpdateSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="title", required=False)
    user_role = serializers.ChoiceField(source="booking_type", choices=Booking.BOOKING_TYPES, required=False)

    class Meta:
        model = Booking
        fields = (
            'item_name',
            'user_role',
            'start_date',
            'end_date',
            'status',
        )


# PATCH Status only
class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('status',)

    def validate(self, attrs):
        if attrs['status'] not in ['approved', 'rejected', 'completed', 'cancelled', 'available', 'book', 'pending']:
            raise serializers.ValidationError({'status': 'Invalid status for this action.'})
        return attrs
