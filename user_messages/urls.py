from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.messages_inbox, name='messages-inbox'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation-detail'),
    path('start/<str:username>/', views.start_conversation, name='start-conversation'),
]