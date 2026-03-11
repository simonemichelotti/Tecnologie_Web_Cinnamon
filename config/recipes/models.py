from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image

class Recipe(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Facile'),
        ('medium', 'Medio'),
        ('hard', 'Difficile'),
    ]
    
    CUISINE_TYPES = [
        ('italian', 'Italiana'),
        ('french', 'Francese'),
        ('japanese', 'Giapponese'),
        ('indian', 'Indiana'),
        ('chinese', 'Cinese'),
        ('mediterranean', 'Mediterranea'),
        ('vegan', 'Vegana'),
        ('vegetarian', 'Vegetariana'),
        ('dessert', 'Dolce'),
        ('bread', 'Pane/Lievitato'),
        ('other', 'Altro'),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', 'Pubblica'),
        ('friends', 'Solo Amici'),
        ('private', 'Privata'),
    ]
    
    # Campi base
    title = models.CharField(max_length=200, verbose_name="Titolo")
    description = models.TextField(verbose_name="Descrizione")
    image = models.ImageField(upload_to='recipe_pics', blank=True, null=True, verbose_name="Foto")
    
    # Dettagli ricetta
    ingredients = models.TextField(default="", verbose_name="Ingredienti")
    instructions = models.TextField(default="", verbose_name="Procedimento")
    prep_time = models.PositiveIntegerField(default=30, help_text="Tempo in minuti", verbose_name="Tempo Preparazione")
    cook_time = models.PositiveIntegerField(default=30, help_text="Tempo in minuti", verbose_name="Tempo Cottura")
    servings = models.PositiveIntegerField(default=4, verbose_name="Porzioni")
    
    # Classificazione
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium', verbose_name="Difficoltà")
    cuisine_type = models.CharField(max_length=20, choices=CUISINE_TYPES, default='other', verbose_name="Tipo Cucina")
    tags = models.JSONField(default=list, blank=True, verbose_name="Tags")
    
    # Note e privacy
    personal_notes = models.TextField(blank=True, null=True, verbose_name="Note Personali")
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public', verbose_name="Visibilità")
    
    # Relazioni
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autore")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('recipes-detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image:
            img = Image.open(self.image.path)
            
            if img.height > 400 or img.width > 400:
                output_size = (400, 400)
                img.thumbnail(output_size)
                img.save(self.image.path)
    
    @property
    def total_prep_time(self):
        return self.prep_time + self.cook_time
    
    @property
    def total_likes(self):
        return self.likes.count()
    
    @property  
    def total_dislikes(self):
        return self.dislikes.count()
    
    @property
    def rating_score(self):
        """Calcola un punteggio basato su like e dislike"""
        likes = self.total_likes
        dislikes = self.total_dislikes
        total = likes + dislikes
        if total == 0:
            return 0
        return (likes / total) * 100
    
    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()
    
    def is_disliked_by(self, user):
        return self.dislikes.filter(user=user).exists()
    
    def can_view(self, user):
        """Controlla se un utente può vedere questa ricetta"""
        if self.visibility == 'public':
            return True
        if self.visibility == 'private':
            return user == self.author
        if self.visibility == 'friends':
            if user == self.author:
                return True
            if user.is_authenticated:
                from users.models import Friendship
                return Friendship.are_friends(user, self.author)
        return False

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'recipe')
    
    def __str__(self):
        return f'{self.user.username} likes {self.recipe.title}'


class Dislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='dislikes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'recipe')
    
    def __str__(self):
        return f'{self.user.username} dislikes {self.recipe.title}'


class Comment(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name="Commento")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    # Moderazione
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f'Commento di {self.author.username} su {self.recipe.title}'
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    def get_replies(self):
        return Comment.objects.filter(parent=self, is_approved=True)


# Modelli per le Community
class Community(models.Model):
    VISIBILITY_CHOICES = [
        ('public', 'Pubblica'),
        ('private', 'Privata (su invito)'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    description = models.TextField(verbose_name="Descrizione")
    image = models.ImageField(upload_to='community_pics', blank=True, null=True, verbose_name="Immagine")
    
    # Gestione
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_communities')
    moderators = models.ManyToManyField(User, blank=True, related_name='moderated_communities')
    members = models.ManyToManyField(User, blank=True, related_name='joined_communities')
    
    # Impostazioni
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    is_active = models.BooleanField(default=True)
    
    # Statistiche
    total_posts = models.PositiveIntegerField(default=0)
    total_members = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Communities"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def can_join(self, user):
        """Controlla se un utente può unirsi alla community"""
        if self.visibility == 'public':
            return True
        return False  # Per le private serve un invito
    
    def is_member(self, user):
        return self.members.filter(id=user.id).exists()
    
    def is_moderator(self, user):
        return user == self.creator or self.moderators.filter(id=user.id).exists()


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


# Modelli per la messaggistica
class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    title = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.title:
            return self.title
        return f"Conversazione {self.id}"
    
    def get_latest_message(self):
        return self.messages.first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(verbose_name="Messaggio")
    
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.content[:30] if self.content else ''
