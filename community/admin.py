# Admin per la app community
from django.contrib import admin
from .models import Community, CommunityPost, CommunityComment

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
	list_display = ['name', 'creator', 'visibility', 'is_active', 'created_at']
	list_filter = ['visibility', 'is_active', 'created_at']
	search_fields = ['name', 'description', 'creator__username']
	# filter_horizontal non supportato per ManyToMany con modello intermedio

@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
	list_display = ['title', 'community', 'author', 'created_at', 'is_pinned', 'is_approved', 'is_locked']
	list_filter = ['community', 'is_pinned', 'is_approved', 'is_locked', 'created_at']
	search_fields = ['title', 'content', 'author__username', 'community__name']

@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
	list_display = ['author', 'post', 'content', 'created_at', 'is_approved']
	list_filter = ['is_approved', 'created_at']
	search_fields = ['content', 'author__username', 'post__title']
