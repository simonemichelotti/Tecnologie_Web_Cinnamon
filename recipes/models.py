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
    
    
    


# Like model
class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} likes {self.recipe.title}'

# Dislike model
class Dislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='dislikes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} dislikes {self.recipe.title}'

# Comment model
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




