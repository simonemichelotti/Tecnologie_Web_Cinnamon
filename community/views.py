# Views per la app community
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import Community, CommunityPost, CommunityJoinRequest, CommunityInvite


class CommunityListView(ListView):
	model = Community
	template_name = 'community/community_list.html'
	context_object_name = 'communities'
	paginate_by = 10
	def get_queryset(self):
		from django.db.models import Q
		user = self.request.user
		qs = Community.objects.all()
		if user.is_authenticated:
			from users.models import Friendship
			friend_ids = Friendship.get_friends(user).values_list('id', flat=True)
			qs = qs.filter(
				Q(visibility='public') |
				Q(visibility='private', members=user) |
				Q(visibility='private', moderators=user) |
				Q(visibility='private', creator=user) |
				Q(visibility='private', creator__id__in=friend_ids)
			).distinct()
		else:
			qs = qs.filter(visibility='public')
		return qs.annotate(
			member_count=Count('members')
		).order_by('-member_count', '-created_at')

class CommunityDetailView(DetailView):
	model = Community
	template_name = 'community/community_detail.html'
	context_object_name = 'community'
	def get(self, request, *args, **kwargs):
		community = self.get_object()
		# Se la community è privata, mostra solo a chi ha accesso
		if not community.can_view(request.user):
			return render(request, 'community/private_community_denied.html', {'community': community})
		return super().get(request, *args, **kwargs)
	def get_context_data(self, **kwargs):
			context = super().get_context_data(**kwargs)
			community = self.get_object()
			context['posts'] = community.posts.filter(is_approved=True).annotate(
				vote_score=Count('upvotes') - Count('downvotes')
			).order_by('-is_pinned', '-vote_score', '-created_at')[:20]
			context['is_member'] = self.request.user in community.members.all() if self.request.user.is_authenticated else False
			context['is_moderator'] = self.request.user in community.moderators.all() if self.request.user.is_authenticated else False
			# Add pending invites count for notification badge
			invites_count = 0
			if self.request.user.is_authenticated:
				invites_count = CommunityInvite.objects.filter(to_user=self.request.user, status='pending').count()
			context['invites_count'] = invites_count
			return context

class CommunityCreateView(LoginRequiredMixin, CreateView):
	model = Community
	template_name = 'community/community_form.html'
	fields = ['name', 'description', 'visibility']
	def form_valid(self, form):
		form.instance.creator = self.request.user
		response = super().form_valid(form)
		form.instance.moderators.add(self.request.user)
		form.instance.members.add(self.request.user)
		return response
	def get_success_url(self):
		return reverse_lazy('community-detail', kwargs={'pk': self.object.pk})

@login_required
def join_community(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if community.visibility == 'private':
		messages.error(request, "Questa community è privata. Devi richiedere l'accesso.")
		return redirect('community-detail', pk=pk)
	if request.user not in community.members.all():
		community.members.add(request.user)
	return redirect('community-detail', pk=pk)

@login_required  
def leave_community(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if request.user in community.members.all():
		community.members.remove(request.user)
	return redirect('community-detail', pk=pk)

@login_required
def create_community_post(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if request.user not in community.members.all():
		messages.error(request, "Devi essere membro della community per pubblicare.")
		return redirect('community-detail', pk=pk)
	if request.method == 'POST':
		content = request.POST.get('content')
		title = request.POST.get('title', '')
		if content:
			post = CommunityPost.objects.create(
				community=community,
				author=request.user,
				title=title,
				content=content
			)
			messages.success(request, "Post pubblicato con successo!")
		else:
			messages.error(request, "Il contenuto del post non può essere vuoto.")
	return redirect('community-detail', pk=pk)

@login_required
def manage_community(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if request.user not in community.moderators.all() and request.user != community.creator:
		messages.error(request, "Non hai i permessi per gestire questa community.")
		return redirect('community-detail', pk=pk)
	pending_requests = community.join_requests.filter(status='pending')
	context = {
		'community': community,
		'is_creator': request.user == community.creator,
		'is_moderator': request.user in community.moderators.all(),
		'pending_posts': community.posts.filter(is_approved=False),
		'flagged_posts': community.posts.filter(is_approved=True),
		'member_count': community.members.count(),
		'post_count': community.posts.count(),
		'pending_requests': pending_requests,
		'pending_requests_count': pending_requests.count(),
	}
	return render(request, 'community/community_manage.html', context)

@login_required
def approve_post(request, community_pk, post_pk):
	community = get_object_or_404(Community, pk=community_pk)
	post = get_object_or_404(CommunityPost, pk=post_pk, community=community)
	if request.user not in community.moderators.all() and request.user != community.creator:
		messages.error(request, "Non hai i permessi per moderare questa community.")
		return redirect('community-detail', pk=community_pk)
	if request.method == 'POST':
		action = request.POST.get('action')
		if action == 'approve':
			post.is_approved = True
			post.save()
			messages.success(request, "Post approvato con successo.")
		elif action == 'delete':
			post.delete()
			messages.success(request, "Post eliminato con successo.")
	return redirect('community-manage', pk=community_pk)

@login_required
def update_community_settings(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if not (request.user == community.creator or community.is_moderator(request.user)):
		messages.error(request, "Solo il creatore o i moderatori possono modificare le impostazioni della community.")
		return redirect('community-detail', pk=pk)
	if request.method == 'POST':
		name = request.POST.get('name')
		description = request.POST.get('description')
		visibility = request.POST.get('visibility')
		if name and description:
			community.name = name
			community.description = description
			community.visibility = visibility
			community.save()
			messages.success(request, "Impostazioni community aggiornate con successo.")
		else:
			messages.error(request, "Nome e descrizione sono obbligatori.")
	return redirect('community-manage', pk=pk)

@login_required
def promote_to_moderator(request, community_pk, user_pk):
	community = get_object_or_404(Community, pk=community_pk)
	user_to_promote = get_object_or_404(User, pk=user_pk)
	if request.user != community.creator:
		messages.error(request, "Solo il creatore può promuovere moderatori.")
		return redirect('community-manage', pk=community_pk)
	if request.method == 'POST':
		if user_to_promote in community.members.all():
			community.moderators.add(user_to_promote)
			messages.success(request, f"{user_to_promote.username} è stato promosso a moderatore.")
		else:
			messages.error(request, "L'utente deve essere membro della community.")
	return redirect('community-manage', pk=community_pk)

@login_required
def remove_moderator(request, community_pk, user_pk):
	community = get_object_or_404(Community, pk=community_pk)
	user_to_demote = get_object_or_404(User, pk=user_pk)
	if request.user != community.creator:
		messages.error(request, "Solo il creatore può rimuovere moderatori.")
		return redirect('community-manage', pk=community_pk)
	if request.method == 'POST':
		if user_to_demote in community.moderators.all():
			community.moderators.remove(user_to_demote)
			messages.success(request, f"{user_to_demote.username} non è più moderatore.")
		else:
			messages.error(request, "L'utente non è un moderatore.")
	return redirect('community-manage', pk=community_pk)

@login_required
def remove_member(request, community_pk, user_pk):
	community = get_object_or_404(Community, pk=community_pk)
	user_to_remove = get_object_or_404(User, pk=user_pk)
	if request.user != community.creator and request.user not in community.moderators.all():
		messages.error(request, "Non hai i permessi per rimuovere membri.")
		return redirect('community-manage', pk=community_pk)
	if user_to_remove == community.creator:
		messages.error(request, "Non puoi rimuovere il creatore della community.")
		return redirect('community-manage', pk=community_pk)
	if request.method == 'POST':
		if user_to_remove in community.members.all():
			community.members.remove(user_to_remove)
			if user_to_remove in community.moderators.all():
				community.moderators.remove(user_to_remove)
			messages.success(request, f"{user_to_remove.username} è stato rimosso dalla community.")
		else:
			messages.error(request, "L'utente non è membro della community.")
	return redirect('community-manage', pk=community_pk)

# Espulsione e promozione membri (moderatori e gestore)
@login_required
def manage_members(request, pk):
	community = get_object_or_404(Community, pk=pk)
	user = request.user
	if not community.is_moderator(user):
		messages.error(request, "Solo i moderatori possono gestire i membri.")
		return redirect('community-detail', pk=pk)
	members = community.members.exclude(id=community.creator.id)
	if request.method == 'POST':
		member_id = request.POST.get('member_id')
		action = request.POST.get('action')
		member = get_object_or_404(User, id=member_id)
		if action == 'remove':
			community.members.remove(member)
			community.moderators.remove(member)  # Rimuovi anche da moderatore se lo era
			messages.success(request, f"{member.username} è stato espulso dalla community.")
		elif action == 'promote':
			community.moderators.add(member)
			messages.success(request, f"{member.username} è stato promosso a moderatore.")
		elif action == 'demote':
			community.moderators.remove(member)
			messages.info(request, f"{member.username} non è più moderatore.")
		return redirect('community-manage-members', pk=pk)
	return render(request, 'community/manage_members.html', {'community': community, 'members': members})

# Invio invito (moderatore)
@login_required
def send_invite(request, pk):
	community = get_object_or_404(Community, pk=pk)
	user = request.user
	if not community.is_moderator(user):
		messages.error(request, "Solo i moderatori possono invitare amici.")
		return redirect('community-detail', pk=pk)
	from users.models import Friendship
	friends = Friendship.get_friends(user)
	if request.method == 'POST':
		friend_id = request.POST.get('friend_id')
		friend = get_object_or_404(User, id=friend_id)
		existing_invite = CommunityInvite.objects.filter(community=community, to_user=friend).first()
		if existing_invite:
			if existing_invite.status == 'pending':
				messages.info(request, f"Hai già inviato un invito a {friend.username}.")
			else:
				# Invito precedente accettato/rifiutato: resetta a pending
				existing_invite.status = 'pending'
				existing_invite.from_user = user
				existing_invite.save()
				messages.success(request, f"Invito re-inviato a {friend.username}.")
		else:
			CommunityInvite.objects.create(community=community, from_user=user, to_user=friend)
			messages.success(request, f"Invito inviato a {friend.username}.")
			# Notifica all'utente invitato
			from users.models import Notification
			Notification.objects.create(
				recipient=friend,
				message=f"{user.username} ti ha invitato nella community '{community.name}'.",
				link=f"/community/invites/"
			)
		return redirect('community-send-invite', pk=pk)
	return render(request, 'community/send_invite.html', {'community': community, 'friends': friends})

# Gestione inviti ricevuti (utente)
@login_required
def received_invites(request):
	invites = CommunityInvite.objects.filter(to_user=request.user, status='pending').select_related('community', 'from_user')
	if request.method == 'POST':
		invite_id = request.POST.get('invite_id')
		action = request.POST.get('action')
		invite = get_object_or_404(CommunityInvite, id=invite_id, to_user=request.user)
		if action == 'accept':
			invite.status = 'accepted'
			invite.community.members.add(request.user)
			messages.success(request, f"Sei entrato nella community {invite.community.name}.")
		elif action == 'reject':
			invite.status = 'rejected'
			messages.info(request, f"Invito per {invite.community.name} rifiutato.")
		invite.save()
		return redirect('community-received-invites')
	return render(request, 'community/received_invites.html', {'invites': invites})

# Invita amici nella community (moderatori e gestore)
@login_required
def invite_friend_to_community(request, pk):
	community = get_object_or_404(Community, pk=pk)
	user = request.user
	# Solo moderatori e gestore
	if not community.is_moderator(user):
		messages.error(request, "Solo i moderatori possono invitare amici.")
		return redirect('community-detail', pk=pk)
	# Lista amici
	from users.models import Friendship
	friends = Friendship.get_friends(user)
	if request.method == 'POST':
		friend_id = request.POST.get('friend_id')
		friend = get_object_or_404(User, id=friend_id)
		if community.is_member(friend):
			messages.info(request, f"{friend.username} è già membro.")
		else:
			community.members.add(friend)
			messages.success(request, f"{friend.username} è stato invitato nella community.")
		return redirect('community-invite', pk=pk)
	return render(request, 'community/invite_friend.html', {'community': community, 'friends': friends})

# Gestione richieste di accesso (solo gestore)
@login_required
def manage_join_requests(request, pk):
	community = get_object_or_404(Community, pk=pk)
	if request.user != community.creator:
		messages.error(request, "Solo il gestore può gestire le richieste.")
		return redirect('community-detail', pk=pk)
	requests = community.join_requests.filter(status='pending').select_related('user')
	if request.method == 'POST':
		action = request.POST.get('action')
		req_id = request.POST.get('request_id')
		join_request = get_object_or_404(CommunityJoinRequest, id=req_id, community=community)
		if action == 'accept':
			join_request.status = 'accepted'
			join_request.save()
			community.members.add(join_request.user)
			messages.success(request, f"{join_request.user.username} è stato aggiunto alla community.")
		elif action == 'reject':
			join_request.status = 'rejected'
			join_request.save()
			messages.info(request, f"Richiesta di {join_request.user.username} rifiutata.")
		return redirect('community-manage-requests', pk=pk)
	return render(request, 'community/manage_join_requests.html', {'community': community, 'requests': requests})

# View per richiesta di accesso
@login_required
@require_POST
def request_access_to_community(request, pk):
	community = get_object_or_404(Community, pk=pk)
	user = request.user
	# Non permettere richiesta se già membro
	if community.is_member(user):
		messages.info(request, "Sei già membro della community.")
		return redirect('community-detail', pk=pk)
	# Controlla se esiste già una richiesta (qualsiasi stato)
	existing = CommunityJoinRequest.objects.filter(community=community, user=user).first()
	if existing:
		if existing.status == 'pending':
			messages.info(request, "Hai già una richiesta in attesa.")
		else:
			# Richiesta precedente rifiutata: resetta a pending
			existing.status = 'pending'
			existing.save()
			messages.success(request, "Richiesta re-inviata al gestore.")
			# Notifica al creatore della community
			from users.models import Notification
			Notification.objects.create(
				recipient=community.creator,
				message=f"{user.username} ha richiesto di entrare nella community '{community.name}'.",
				link=f"/community/{community.pk}/manage-requests/"
			)
		return redirect('community-detail', pk=pk)
	# Crea nuova richiesta
	CommunityJoinRequest.objects.create(community=community, user=user)
	# Notifica al creatore della community
	from users.models import Notification
	Notification.objects.create(
		recipient=community.creator,
		message=f"{user.username} ha richiesto di entrare nella community '{community.name}'.",
		link=f"/community/{community.pk}/manage-requests/"
	)
	messages.success(request, "Richiesta inviata al gestore.")
	return redirect('community-detail', pk=pk)
