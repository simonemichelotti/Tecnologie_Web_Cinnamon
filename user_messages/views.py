from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Max
from .models import Conversation, Message

@login_required
def messages_inbox(request):
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    unread_counts = {}
    other_users = []
    for conv in conversations:
        unread = Message.objects.filter(conversation=conv, is_read=False).exclude(sender=request.user).count()
        unread_counts[conv.id] = unread
        other = conv.participants.exclude(id=request.user.id).first()
        other_users.append(other)
    context = {
        'conversations': zip(conversations, other_users),
        'unread_counts': unread_counts,
        'title': 'Messaggi'
    }
    return render(request, 'user_messages/messages_inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    Message.objects.filter(
        conversation=conversation, 
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            return redirect('conversation-detail', conversation_id=conversation_id)
    chat_messages = conversation.messages.all().order_by('created_at')
    destinatario = conversation.participants.exclude(id=request.user.id).first()
    titolo_chat = destinatario.get_full_name() if destinatario and destinatario.get_full_name() else destinatario.username if destinatario else 'Chat'
    context = {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'title': titolo_chat,
    }
    return render(request, 'user_messages/conversation_detail.html', context)

@login_required
def start_conversation(request, username):
    try:
        other_user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('messages-inbox')

    # Cerca una conversazione esistente
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        conversation.save()
    return redirect('conversation-detail', conversation_id=conversation.id)