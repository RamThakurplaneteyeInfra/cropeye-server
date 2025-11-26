from django.db import models


class ChatbotConfig(models.Model):
    """Configuration settings for the chatbot service"""
    model_name = models.CharField(
        max_length=100,
        default="llama3.1",
        help_text="Ollama model name to use"
    )
    api_url = models.URLField(
        default="http://localhost:11434/api/generate",
        help_text="Ollama API endpoint URL"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Enable/disable chatbot service"
    )
    timeout_seconds = models.IntegerField(
        default=30,
        help_text="Request timeout in seconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chatbot Configuration"
        verbose_name_plural = "Chatbot Configurations"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chatbot Config ({self.model_name})"

    def save(self, *args, **kwargs):
        if self.is_active:
            ChatbotConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
