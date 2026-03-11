from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('recipes.urls')),
    
    # Authentication URLs
    path('register/', user_views.register, name="user-register"),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name="user-login"),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name="user-logout"),
    
    # User Profile URLs
    path('profile/', user_views.profile, name="user-profile"),
    path('profile/update/', user_views.update_profile, name="user-update-profile"),
    path('users/search/', user_views.user_search, name="user-search"),
    path('users/<str:username>/', user_views.public_profile, name="user-public-profile"),
    
    # Friend System URLs
    path('friends/', user_views.friends_list, name="user-friends"),
    path('friends/requests/', user_views.friend_requests, name="user-friend-requests"),
    path('friends/add/<str:username>/', user_views.send_friend_request, name="user-send-friend-request"),
    path('friends/accept/<int:request_id>/', user_views.accept_friend_request, name="user-accept-friend-request"),
    path('friends/reject/<int:request_id>/', user_views.reject_friend_request, name="user-reject-friend-request"),
    
    # Messaging URLs
    path('messages/', user_views.messages_inbox, name="messages-inbox"),
    path('messages/<int:conversation_id>/', user_views.conversation_detail, name="conversation-detail"),
    path('messages/start/<str:username>/', user_views.start_conversation, name="start-conversation"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)