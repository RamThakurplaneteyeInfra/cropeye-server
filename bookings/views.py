from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Booking, BookingComment, BookingAttachment
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingUpdateSerializer,
    BookingStatusUpdateSerializer,
    BookingCommentSerializer,
    BookingCommentCreateSerializer,
    BookingAttachmentSerializer,
    BookingAttachmentCreateSerializer
)
from .permissions import CanManageBookings, CanViewBookings
from users.multi_tenant_utils import filter_by_industry, get_user_industry

class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'booking_type']
    search_fields = ['title', 'item_name', 'description']
    ordering_fields = ['start_date', 'end_date', 'created_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BookingUpdateSerializer
        elif self.action == 'update_status':
            return BookingStatusUpdateSerializer
        return BookingSerializer

    def get_permissions(self):
        action = getattr(self, 'action', 'list')
        if action in ['create', 'destroy']:
            return [CanManageBookings()]
        elif action in ['update', 'partial_update']:
            return [CanManageBookings()]
        elif action == 'update_status':
            return [CanManageBookings()]
        return [CanViewBookings()]

    def get_queryset(self):
        qs = Booking.objects.all()
        user = self.request.user
        
        # Apply multi-tenant filtering by industry
        qs = filter_by_industry(qs, user)
        
        # Filter by status
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        
        # Filter by booking_type
        booking_type = self.request.query_params.get('booking_type')
        if booking_type:
            qs = qs.filter(booking_type=booking_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            qs = qs.filter(start_date__gte=start_date)
        
        if end_date:
            qs = qs.filter(end_date__lte=end_date)
        
        # Filter by date (for bookings on a specific date)
        date = self.request.query_params.get('date')
        if date:
            qs = qs.filter(
                start_date__date__lte=date,
                end_date__date__gte=date
            )
        
        # Search parameter
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(item_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        # Additional filtering for non-admin/manager/field officer users
        if not (user.is_superuser or user.has_role('owner') or user.has_role('manager') or user.has_role('fieldofficer')):
            # Regular users can only see their own bookings
            qs = qs.filter(created_by=user)
        
        return qs.select_related('created_by', 'approved_by', 'industry')

    def perform_create(self, serializer):
        user = self.request.user
        # Get user's industry and auto-assign it to the booking
        user_industry = get_user_industry(user)
        
        # For non-superusers, always use their industry (ignore any industry_id from request)
        # Superusers can specify industry_id if needed, otherwise use their industry
        if not user.is_superuser or 'industry' not in serializer.validated_data:
            # Auto-assign industry from user (for non-superusers or superusers without explicit industry)
            if user_industry:
                serializer.save(created_by=user, industry=user_industry)
            else:
                serializer.save(created_by=user)
        else:
            # Superuser provided explicit industry
            serializer.save(created_by=user)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingCommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(booking=booking, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingAttachmentCreateSerializer(data=request.data, files=request.FILES)
        if serializer.is_valid():
            serializer.save(booking=booking, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        booking = self.get_object()
        serializer = BookingStatusUpdateSerializer(data=request.data)
        if serializer.is_valid():
            booking.status = serializer.validated_data['status']
            if booking.status in ['approved', 'rejected']:
                booking.approved_by = request.user
            booking.save()
            return Response(BookingSerializer(booking).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BookingCommentViewSet(viewsets.ModelViewSet):
    serializer_class = BookingCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BookingComment.objects.filter(booking_id=self.kwargs['booking_pk'])

    def perform_create(self, serializer):
        booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        serializer.save(booking=booking, user=self.request.user)

class BookingAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = BookingAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BookingAttachment.objects.filter(booking_id=self.kwargs['booking_pk'])

    def perform_create(self, serializer):
        booking = get_object_or_404(Booking, pk=self.kwargs['booking_pk'])
        serializer.save(booking=booking, uploaded_by=self.request.user) 