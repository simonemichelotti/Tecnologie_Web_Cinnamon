from django.db import models
from django.contrib.auth.models import User
from PIL import Image

class UserProfile(models.Model):
    EXPERIENCE_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'), 
        ('advanced', 'Avanzato'),
        ('professional', 'Professionale'),
    ]
    
    CUISINE_SPECIALTIES = [
        ('italian', 'Cucina Italiana'),
        ('french', 'Cucina Francese'),
        ('japanese', 'Cucina Giapponese'),
        ('indian', 'Cucina Indiana'),
        ('chinese', 'Cucina Cinese'),
        ('mediterranean', 'Cucina Mediterranea'),
        ('vegan', 'Cucina Vegana'),
        ('vegetarian', 'Cucina Vegetariana'),
        ('desserts', 'Dolci e Dessert'),
        ('bread', 'Pane e Lievitati'),
        ('pastry', 'Pasticceria'),
        ('bbq', 'Barbecue e Grigliata'),
        ('fusion', 'Cucina Fusion'),
        ('raw', 'Cucina Crudista'),
        ('gluten_free', 'Senza Glutine'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, null=True, verbose_name="Biografia")
    profile_image = models.ImageField(upload_to='profile_pics', blank=True, null=True, verbose_name="Foto Profilo")
    
    # Cucina e competenze
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner', verbose_name="Livello Esperienza")
    cuisine_specialties = models.JSONField(default=list, blank=True, verbose_name="Specialità Culinarie")
    culinary_interests = models.TextField(blank=True, null=True, verbose_name="Interessi Gastronomici")
    
    # Privacy
    is_public = models.BooleanField(default=True, verbose_name="Profilo Pubblico")
    show_email = models.BooleanField(default=False, verbose_name="Mostra Email")
    
    # Informazioni aggiuntive
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="Località")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data di Nascita")
    
    # Social
    website = models.URLField(blank=True, null=True, verbose_name="Sito Web")
    instagram = models.CharField(max_length=50, blank=True, null=True, verbose_name="Instagram")
    
    # Statistiche (campi rimossi, ora sono proprietà dinamiche)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profilo di {self.user.username}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.profile_image and hasattr(self.profile_image, 'path'):
            try:
                img = Image.open(self.profile_image.path)
                
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.profile_image.path)
            except (IOError, OSError):
                # Se c'è un errore nell'aprire l'immagine, ignoriamolo per ora
                pass
    
    @property
    def total_recipes(self):
        from recipes.models import Recipe
        return Recipe.objects.filter(author=self.user).count()
    
    @property
    def friends_count(self):
        return Friendship.get_friends(self.user).count()
    
    @property
    def total_likes_received(self):
        from recipes.models import Like
        return Like.objects.filter(recipe__author=self.user).count()
    
    def get_specialties_display(self):
        """Ritorna le specialità in formato leggibile"""
        if not self.cuisine_specialties:
            return []
        specialty_dict = dict(self.CUISINE_SPECIALTIES)
        return [specialty_dict.get(spec, spec) for spec in self.cuisine_specialties]


class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'In Attesa'),
        ('accepted', 'Accettata'),
        ('rejected', 'Rifiutata'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, null=True, max_length=200, verbose_name="Messaggio")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
        
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"
        
    def accept(self):
        """Accetta la richiesta di amicizia e crea la relazione bidirezionale"""
        self.status = 'accepted'
        self.save()
        
        # Crea entrambe le direzioni della relazione di amicizia
        Friendship.objects.get_or_create(
            user=self.from_user,
            friend=self.to_user
        )
        Friendship.objects.get_or_create(
            user=self.to_user,
            friend=self.from_user
        )
        
    def reject(self):
        """Rifiuta la richiesta di amicizia"""
        self.status = 'rejected'
        self.save()


class Friendship(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_of')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'friend')
    
    def __str__(self):
        return f"{self.user.username} è amico di {self.friend.username}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.user == self.friend:
            raise ValidationError("Un utente non può essere amico di se stesso.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    @classmethod
    def are_friends(cls, user1, user2):
        """Verifica se due utenti sono amici"""
        return cls.objects.filter(
            models.Q(user=user1, friend=user2) | 
            models.Q(user=user2, friend=user1)
        ).exists()
    
    @classmethod
    def get_friends(cls, user):
        """Ottiene tutti gli amici di un utente"""
        friend_ids = cls.objects.filter(
            models.Q(user=user) | models.Q(friend=user)
        ).values_list('user', 'friend')
        
        all_friend_ids = set()
        for user_id, friend_id in friend_ids:
            if user_id == user.id:
                all_friend_ids.add(friend_id)
            else:
                all_friend_ids.add(user_id)
                
        return User.objects.filter(id__in=all_friend_ids)
