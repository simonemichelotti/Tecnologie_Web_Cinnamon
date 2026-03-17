# Urls per la app community
from django.urls import path
from . import views

urlpatterns = [
	path('communities/', views.CommunityListView.as_view(), name='community-list'),
	path('community/<int:pk>/', views.CommunityDetailView.as_view(), name='community-detail'),
	path('community/create/', views.CommunityCreateView.as_view(), name='community-create'),
	path('community/<int:pk>/join/', views.join_community, name='community-join'),
	path('community/<int:pk>/request-access/', views.request_access_to_community, name='community-request-access'),
	path('community/<int:pk>/leave/', views.leave_community, name='community-leave'),
	path('community/<int:pk>/post/', views.create_community_post, name='community-create-post'),
	path('community/<int:pk>/manage/', views.manage_community, name='community-manage'),
	path('community/<int:pk>/manage-requests/', views.manage_join_requests, name='community-manage-requests'),
	path('community/<int:community_pk>/post/<int:post_pk>/moderate/', views.approve_post, name='community-approve-post'),
	path('community/<int:pk>/settings/', views.update_community_settings, name='community-update-settings'),
	path('community/<int:community_pk>/promote/<int:user_pk>/', views.promote_to_moderator, name='community-promote-moderator'),
	path('community/<int:community_pk>/demote/<int:user_pk>/', views.remove_moderator, name='community-remove-moderator'),
	path('community/<int:community_pk>/remove/<int:user_pk>/', views.remove_member, name='community-remove-member'),
	path('community/<int:pk>/manage-members/', views.manage_members, name='community-manage-members'),
	path('community/<int:pk>/send-invite/', views.send_invite, name='community-send-invite'),
	path('community/invites/', views.received_invites, name='community-received-invites'),
	path('community/<int:pk>/invite/', views.invite_friend_to_community, name='community-invite'),
]
