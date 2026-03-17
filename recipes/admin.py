
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
    list_display = ['author', 'recipe', 'content', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'is_flagged', 'created_at']
    search_fields = ['content', 'author__username', 'recipe__title']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content


