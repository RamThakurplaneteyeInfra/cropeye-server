from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Booking, BookingComment, BookingAttachment
from users.serializers import IndustrySerializer, RoleSerializer
from users.models import Industry, Role

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name')

class BookingCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = BookingComment
        fields = ('id', 'user', 'content', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class BookingAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = BookingAttachment
        fields = ('id', 'file', 'uploaded_by', 'uploaded_at', 'description')
        read_only_fields = ('uploaded_at',)

class BookingSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    industry = IndustrySerializer(read_only=True)
    user_role = RoleSerializer(read_only=True)
    comments = BookingCommentSerializer(many=True, read_only=True)
    attachments = BookingAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Booking
        fields = ('id', 'title', 'item_name', 'description', 'booking_type', 'status',
                 'start_date', 'end_date', 'industry', 'user_role', 'created_by', 'approved_by',
                 'created_at', 'updated_at', 'comments', 'attachments')
        read_only_fields = ('created_at', 'updated_at', 'approved_by', 'industry', 'user_role')

class BookingCreateSerializer(serializers.ModelSerializer):
    # Industry is optional - will be auto-assigned from user if not provided
    industry_id = serializers.PrimaryKeyRelatedField(
        source='industry',
        queryset=Industry.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    # User role is optional
    user_role_id = serializers.PrimaryKeyRelatedField(
        source='user_role',
        queryset=Role.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )

    class Meta:
        model = Booking
        fields = ('title', 'item_name', 'description', 'booking_type', 'start_date', 'end_date', 'industry_id', 'user_role_id', 'status')

class BookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('title', 'item_name', 'description', 'booking_type', 'start_date', 'end_date')

class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('status',)

    def validate(self, attrs):
        if attrs['status'] not in ['approved', 'rejected', 'completed', 'cancelled']:
            raise serializers.ValidationError({'status': 'Invalid status for this action.'})
        return attrs

class BookingCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingComment
        fields = ('content',)

class BookingAttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAttachment
        fields = ('file', 'description') 