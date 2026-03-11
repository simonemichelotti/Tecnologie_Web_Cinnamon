from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'cuisine_type', 'difficulty', 'visibility', 'created_at']
    list_filter = ['cuisine_type', 'difficulty', 'visibility', 'created_at']
    search_fields = ['title', 'description', 'author__username']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(models.Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']

@admin.register(models.Dislike)  
class DislikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'recipe', 'created_at']
    list_filter = ['created_at']

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'recipe', 'content_preview', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'is_flagged', 'created_at']
    search_fields = ['content', 'author__username', 'recipe__title']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

@admin.register(models.Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'visibility', 'total_members', 'is_active', 'created_at']
    list_filter = ['visibility', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'creator__username']
    filter_horizontal = ['moderators', 'members']

@admin.register(models.CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'community', 'author', 'score', 'is_pinned', 'created_at']
    list_filter = ['community', 'is_pinned', 'is_approved', 'created_at']
    search_fields = ['title', 'content', 'author__username']

@admin.register(models.CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'content_preview', 'score', 'created_at']
    list_filter = ['is_approved', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

@admin.register(models.Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at', 'updated_at']
    filter_horizontal = ['participants']

@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

