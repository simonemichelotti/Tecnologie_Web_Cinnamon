
from django.db import models
from django.contrib.auth.models import User

# Modelli per la app community


# Definizione della classe Community
class Community(models.Model):
	VISIBILITY_CHOICES = [
		('public', 'Pubblica'),
		('private', 'Privata (su invito)'),
	]
	name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
	description = models.TextField(verbose_name="Descrizione")
	image = models.ImageField(upload_to='community_pics', blank=True, null=True, verbose_name="Immagine")
	creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities')
	moderators = models.ManyToManyField(User, through='Community_moderators', related_name='moderated_communities', blank=True)
	members = models.ManyToManyField(User, through='Community_members', related_name='joined_communities', blank=True)
	visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		verbose_name_plural = "Communities"
		ordering = ['-created_at']
	def __str__(self):
		return self.name
	def can_join(self, user):
		if self.visibility == 'public':
			return True
		return False
	def is_member(self, user):
		return self.members.filter(id=user.id).exists()
	def is_moderator(self, user):
		return user == self.creator or self.moderators.filter(id=user.id).exists()

	def can_view(self, user):
		"""Controlla se un utente può vedere questa community.
		Pubblica: visibile a tutti.
		Privata: visibile solo a membri, moderatori e amici del creatore."""
		if self.visibility == 'public':
			return True
		if not user or not user.is_authenticated:
			return False
		if self.is_member(user) or self.is_moderator(user):
			return True
		from users.models import Friendship
		return Friendship.are_friends(user, self.creator)

# Modello intermedio per membri
class Community_members(models.Model):
	community = models.ForeignKey(Community, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	joined_at = models.DateTimeField(auto_now_add=True)
	class Meta:
		unique_together = ('community', 'user')
	def __str__(self):
		return f"{self.user.username} membro di {self.community.name}"

# Modello intermedio per moderatori
class Community_moderators(models.Model):
	community = models.ForeignKey(Community, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	promoted_at = models.DateTimeField(auto_now_add=True)
	class Meta:
		unique_together = ('community', 'user')
	def __str__(self):
		return f"{self.user.username} moderatore di {self.community.name}"

# Invito attivo a community privata
class CommunityInvite(models.Model):
	STATUS_CHOICES = [
		('pending', 'In attesa'),
		('accepted', 'Accettato'),
		('rejected', 'Rifiutato'),
	]
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='invites')
	from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
	to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_invites')
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		unique_together = ('community', 'to_user')
	def __str__(self):
		return f"Invito da {self.from_user.username} a {self.to_user.username} per {self.community.name} ({self.status})"



# Richiesta di accesso a community privata
class CommunityJoinRequest(models.Model):
	STATUS_CHOICES = [
		('pending', 'In attesa'),
		('accepted', 'Accettata'),
		('rejected', 'Rifiutata'),
	]
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='join_requests')
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='community_join_requests')
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
	message = models.TextField(blank=True, null=True, max_length=200)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		unique_together = ('community', 'user')
	def __str__(self):
		return f"Richiesta di {self.user.username} per {self.community.name} ({self.status})"

class CommunityPost(models.Model):
	community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts')
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	title = models.CharField(max_length=200, verbose_name="Titolo")
	content = models.TextField(verbose_name="Contenuto")
	image = models.ImageField(upload_to='community_posts', blank=True, null=True)
	# Voti stile Reddit
	upvotes = models.ManyToManyField(User, blank=True, related_name='upvoted_posts')
	downvotes = models.ManyToManyField(User, blank=True, related_name='downvoted_posts')
	# Moderazione
	is_pinned = models.BooleanField(default=False)
	is_approved = models.BooleanField(default=True)
	is_locked = models.BooleanField(default=False)  # Blocca commenti
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['-is_pinned', '-created_at']
	def __str__(self):
		return f'{self.title} in {self.community.name}'
	@property
	def score(self):
		return self.upvotes.count() - self.downvotes.count()
	@property
	def total_votes(self):
		return self.upvotes.count() + self.downvotes.count()

class CommunityComment(models.Model):
	post = models.ForeignKey(CommunityPost, on_delete=models.CASCADE, related_name='comments')
	author = models.ForeignKey(User, on_delete=models.CASCADE)
	content = models.TextField(verbose_name="Commento")
	parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
	# Voti
	upvotes = models.ManyToManyField(User, blank=True, related_name='upvoted_comments')
	downvotes = models.ManyToManyField(User, blank=True, related_name='downvoted_comments')
	# Moderazione
	is_approved = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	class Meta:
		ordering = ['created_at']
	def __str__(self):
		return f'Commento di {self.author.username} su {self.post.title}'
	@property
	def score(self):
		return self.upvotes.count() - self.downvotes.count()
