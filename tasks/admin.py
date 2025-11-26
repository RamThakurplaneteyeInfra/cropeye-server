from django.contrib import admin
from .models import Task, TaskComment, TaskAttachment

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'industry', 'status', 'priority', 'assigned_to', 'created_by', 'due_date')
    list_filter = ('industry', 'status', 'priority', 'assigned_to', 'created_by')
    search_fields = ('title', 'description', 'industry__name')
    ordering = ('-created_at',)
    raw_id_fields = ('assigned_to', 'created_by')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'industry', 'status', 'priority', 'assigned_to', 'due_date')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
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

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('content', 'task__title')
    ordering = ('-created_at',)
    raw_id_fields = ('task', 'user')

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_by', 'uploaded_at')
    search_fields = ('description', 'task__title')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('task', 'uploaded_by') 