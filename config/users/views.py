from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max

from . import forms
from .models import UserProfile, FriendRequest, Friendship

# Context processor per notifiche messaggi non letti
from django.db.models import Q

def unread_messages_count(request):
    if request.user.is_authenticated:
        from recipes.models import Conversation, Message
        conversations = Conversation.objects.filter(participants=request.user)
        unread_count = Message.objects.filter(
            conversation__in=conversations,
            is_read=False
        ).exclude(sender=request.user).count()
        return {'unread_messages_count': unread_count}
    return {'unread_messages_count': 0}

def register(request):
    if request.method == "POST":
        form = forms.UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crea automaticamente il profilo utente
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            messages.success(request, f"Benvenuto {username}! Il tuo account è stato creato. Ora puoi accedere.")
            return redirect('user-login')
    else:
        form = forms.UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    context = {
        'profile': profile,
        'user': request.user
    }
    return render(request, 'users/profile.html', context)

@login_required
def update_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = forms.UserUpdateForm(request.POST, instance=request.user)
        p_form = forms.ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Il tuo profilo è stato aggiornato con successo!')
            return redirect('user-profile')
    else:
        u_form = forms.UserUpdateForm(instance=request.user)
        p_form = forms.ProfileUpdateForm(instance=profile)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile
    }
    return render(request, 'users/update_profile.html', context)

@login_required  
def user_search(request):
    """Ricerca utenti per specialità, esperienza e interessi"""
    query = request.GET.get('q', '')
    experience = request.GET.get('experience', '')
    specialty = request.GET.get('specialty', '')
    
    users = User.objects.filter(userprofile__is_public=True).exclude(id=request.user.id)
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(userprofile__bio__icontains=query) |
            Q(userprofile__culinary_interests__icontains=query) |
            Q(userprofile__location__icontains=query)
        )
    
    if experience:
        users = users.filter(userprofile__experience_level=experience)
        
    if specialty:
        users = users.filter(userprofile__cuisine_specialties__contains=[specialty])
    
    context = {
        'users': users,
        'query': query,
        'experience': experience,
        'specialty': specialty,
        'experience_choices': UserProfile.EXPERIENCE_CHOICES,
        'specialty_choices': UserProfile.CUISINE_SPECIALTIES,
    }
    return render(request, 'users/search.html', context)

def public_profile(request, username):
    """Profilo pubblico di un utente"""
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    
    # Controllo privacy
    can_view_full_profile = (
        profile.is_public or 
        user == request.user or
        (request.user.is_authenticated and Friendship.are_friends(request.user, user))
    )
    
    if not can_view_full_profile:
        messages.warning(request, "Questo profilo è privato.")
        return redirect('recipes-home')
    
    # Ottieni ricette pubbliche o visibili all'utente
    from recipes.models import Recipe
    recipes = Recipe.objects.filter(author=user)
    
    if user != request.user and not (request.user.is_authenticated and Friendship.are_friends(request.user, user)):
        recipes = recipes.filter(visibility='public')
    
    # Statistiche amicizie
    is_friend = False
    friend_request_sent = False
    friend_request_received = False
    
    if request.user.is_authenticated and user != request.user:
        is_friend = Friendship.are_friends(request.user, user)
        friend_request_sent = FriendRequest.objects.filter(
            from_user=request.user, to_user=user, status='pending'
        ).exists()
        friend_request_received = FriendRequest.objects.filter(
            from_user=user, to_user=request.user, status='pending'
        ).exists()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'recipes': recipes[:6],  # Solo le prime 6 ricette
        'total_recipes': recipes.count(),
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
        'can_view_full_profile': can_view_full_profile,
    }
    return render(request, 'users/public_profile.html', context)

@login_required
def send_friend_request(request, username):
    """Invia una richiesta di amicizia"""
    to_user = get_object_or_404(User, username=username)
    
    if to_user == request.user:
        messages.error(request, "Non puoi inviare una richiesta di amicizia a te stesso!")
        return redirect('user-public-profile', username=username)
    
    # Controlla se sono già amici
    if Friendship.are_friends(request.user, to_user):
        messages.info(request, "Siete già amici!")
        return redirect('user-public-profile', username=username)
    
    # Controlla se c'è già una richiesta pendente
    existing_request = FriendRequest.objects.filter(
        from_user=request.user, to_user=to_user, status='pending'
    ).first()
    
    if existing_request:
        messages.info(request, "Hai già inviato una richiesta di amicizia a questo utente.")
        return redirect('user-public-profile', username=username)
    
    # Crea la richiesta
    FriendRequest.objects.create(
        from_user=request.user,
        to_user=to_user,
        message=request.POST.get('message', '')
    )
    
    messages.success(request, f"Richiesta di amicizia inviata a {to_user.username}!")
    return redirect('user-public-profile', username=username)

@login_required
def friend_requests(request):
    """Lista delle richieste di amicizia ricevute"""
    received_requests = FriendRequest.objects.filter(
        to_user=request.user, status='pending'
    ).order_by('-created_at')
    
    sent_requests = FriendRequest.objects.filter(
        from_user=request.user, status='pending'
    ).order_by('-created_at')
    
    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
    }
    return render(request, 'users/friend_requests.html', context)

@login_required  
def accept_friend_request(request, request_id):
    """Accetta una richiesta di amicizia"""
    friend_request = get_object_or_404(
        FriendRequest, id=request_id, to_user=request.user, status='pending'
    )
    
    friend_request.accept()
    messages.success(request, f"Ora sei amico di {friend_request.from_user.username}!")
    return redirect('user-friend-requests')

@login_required
def reject_friend_request(request, request_id):
    """Rifiuta una richiesta di amicizia"""
    friend_request = get_object_or_404(
        FriendRequest, id=request_id, to_user=request.user, status='pending'
    )
    
    friend_request.reject()
    messages.info(request, "Richiesta di amicizia rifiutata.")
    return redirect('user-friend-requests')

@login_required
def friends_list(request):
    """Lista degli amici dell'utente"""
    friends = Friendship.get_friends(request.user)
    
    context = {
        'friends': friends,
    }
    return render(request, 'users/friends_list.html', context)

# Messaging Views
@login_required
def messages_inbox(request):
    """Vista della inbox dei messaggi"""
    from recipes.models import Conversation, Message
    
    # Conversazioni dell'utente ordinate per ultimo messaggio
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__created_at')
    ).order_by('-last_message_time')
    
    # Calcola notifiche: conta messaggi non letti per ogni conversazione
    unread_counts = {}
    other_users = []
    for conv in conversations:
        # Messaggi non letti inviati dagli altri
        unread = Message.objects.filter(conversation=conv, is_read=False).exclude(sender=request.user).count()
        unread_counts[conv.id] = unread
        # Trova l'altro partecipante
        other = conv.participants.exclude(id=request.user.id).first()
        other_users.append(other)

    context = {
        'conversations': zip(conversations, other_users),
        'unread_counts': unread_counts,
        'title': 'Messaggi'
    }
    return render(request, 'users/messages_inbox.html', context)

@login_required  
def conversation_detail(request, conversation_id):
    """Vista dettaglio conversazione"""
    from recipes.models import Conversation, Message
    
    conversation = get_object_or_404(
        Conversation, id=conversation_id, participants=request.user
    )
    
    # Segna i messaggi come letti (tutti i messaggi non dell'utente corrente)
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
    # Trova l'altro partecipante (destinatario)
    destinatario = conversation.participants.exclude(id=request.user.id).first()
    titolo_chat = destinatario.get_full_name() if destinatario and destinatario.get_full_name() else destinatario.username if destinatario else 'Chat'
    context = {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'title': titolo_chat,
    }
    return render(request, 'users/conversation_detail.html', context)

@login_required
def start_conversation(request, username):
    """Inizia una nuova conversazione con un utente"""
    from recipes.models import Conversation
    
    other_user = get_object_or_404(User, username=username)
    
    # Controlla se esiste già una conversazione tra questi utenti
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.set([request.user, other_user])
    
    return redirect('conversation-detail', conversation_id=conversation.id)