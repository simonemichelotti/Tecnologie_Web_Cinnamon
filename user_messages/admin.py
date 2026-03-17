from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'get_participants', 'created_at', 'updated_at']
    search_fields = ['title']
    filter_horizontal = ['participants']

    def get_participants(self, obj):
        return ", ".join([u.username for u in obj.participants.all()])
    get_participants.short_description = 'Partecipanti'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content', 'is_read', 'created_at']
    search_fields = ['content', 'sender__username']
    list_filter = ['is_read', 'created_at']