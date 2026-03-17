from django.contrib import admin
from . import models

# Register your models here.

@admin.register(models.UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'experience_level', 'is_public', 'friends_count', 'total_recipes', 'created_at']
    list_filter = ['experience_level', 'is_public', 'created_at']
    search_fields = ['user__username', 'user__email', 'bio', 'location']
    readonly_fields = ['total_recipes', 'total_likes_received', 'created_at', 'updated_at']

@admin.register(models.FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']

@admin.register(models.Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['user', 'friend', 'created_at']
    search_fields = ['user__username', 'friend__username']

@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['recipient__username', 'message']

