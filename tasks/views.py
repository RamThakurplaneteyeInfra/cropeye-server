from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Task, TaskComment, TaskAttachment
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskCommentSerializer,
    TaskCommentCreateSerializer,
    TaskAttachmentSerializer,
    TaskAttachmentCreateSerializer
)
from .permissions import CanManageTasks, CanViewTasks

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy', 'update', 'partial_update']:
            return [CanManageTasks()]
        return [CanViewTasks()]

    def get_queryset(self):
        user = self.request.user
        # Use has_any_role and has_role methods, plus is_superuser
        if user.is_superuser or user.has_any_role(['admin', 'manager']):
            return Task.objects.all()
        elif user.has_role('fieldofficer'):
            return Task.objects.filter(Q(assigned_to=user) | Q(created_by=user))
        return Task.objects.filter(assigned_to=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to bypass get_queryset filtering
        but still enforce permissions.
        """
        task = get_object_or_404(Task, pk=kwargs['pk'])
        self.check_object_permissions(request, task)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)    

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        task = self.get_object()
        serializer = TaskCommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        task = self.get_object()
        serializer = TaskAttachmentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task, uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        task.status = new_status
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskComment.objects.filter(task_id=self.kwargs['task_pk'])

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        serializer.save(task=task, user=self.request.user)
    def destroy(self, request, *args, **kwargs):
        comment = get_object_or_404(TaskComment, pk=kwargs['pk'])
        self.check_object_permissions(request, comment)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskAttachment.objects.filter(task_id=self.kwargs['task_pk'])

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs['task_pk'])
        serializer.save(task=task, uploaded_by=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        attachment = get_object_or_404(TaskAttachment, pk=kwargs['pk'])
        self.check_object_permissions(request, attachment)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
