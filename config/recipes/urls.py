from django.urls import path
from . import views

urlpatterns = [
    path('', views.RecipeListView.as_view(), name='recipes-home'),
    path('recipe/<int:pk>/', views.RecipeDetailView.as_view(), name='recipes-detail'),
    path('recipe/<int:pk>/comment/', views.add_comment, name='add-comment'),
    path('recipe/create/', views.RecipeCreateView.as_view(), name='recipes-create'),
    path('recipe/<int:pk>/update/', views.RecipeUpdateView.as_view(), name='recipes-update'),
    path('recipe/<int:pk>/delete/', views.RecipeDeleteView.as_view(), name='recipes-delete'),
    path('recipe/<int:recipe_id>/like/', views.toggle_like, name='recipe-like'),
    
    # Community URLs
    path('communities/', views.CommunityListView.as_view(), name='community-list'),
    path('community/<int:pk>/', views.CommunityDetailView.as_view(), name='community-detail'),
    path('community/create/', views.CommunityCreateView.as_view(), name='community-create'),
    path('community/<int:pk>/join/', views.join_community, name='community-join'),
    path('community/<int:pk>/leave/', views.leave_community, name='community-leave'),
    path('community/<int:pk>/post/', views.create_community_post, name='community-create-post'),
    path('community/<int:pk>/manage/', views.manage_community, name='community-manage'),
    path('community/<int:community_pk>/post/<int:post_pk>/moderate/', views.approve_post, name='community-approve-post'),
    path('community/<int:pk>/settings/', views.update_community_settings, name='community-update-settings'),
    path('community/<int:community_pk>/promote/<int:user_pk>/', views.promote_to_moderator, name='community-promote-moderator'),
    path('community/<int:community_pk>/demote/<int:user_pk>/', views.remove_moderator, name='community-remove-moderator'),
    path('community/<int:community_pk>/remove/<int:user_pk>/', views.remove_member, name='community-remove-member'),
]