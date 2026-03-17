from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, F
from . import models
from .models import Recipe, Like
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django import forms

class RecipeListView(ListView):
    @staticmethod
    def timesince_it(dt):
        from django.utils.timesince import timesince
        s = timesince(dt)
        s = s.replace('minutes', 'minuti').replace('minute', 'minuto')
        s = s.replace('hours', 'ore').replace('hour', 'ora')
        s = s.replace('days', 'giorni').replace('day', 'giorno')
        s = s.replace('weeks', 'settimane').replace('week', 'settimana')
        s = s.replace('months', 'mesi').replace('month', 'mese')
        s = s.replace('years', 'anni').replace('year', 'anno')
        return s

    model = models.Recipe
    template_name = 'recipes/home.html'
    context_object_name = 'recipes'
    paginate_by = 12  # Paginazione per performance
    
    def get_queryset(self):
        """
        Logica personalizzata per la home:
        - Utenti loggati: ricette più votate degli amici + ricette pubbliche
        - Utenti anonimi: solo ricette pubbliche più votate
        """
        queryset = models.Recipe.objects.select_related('author').prefetch_related('likes', 'dislikes')
        
        if self.request.user.is_authenticated:
            # Per utenti loggati: ricette degli amici + ricette pubbliche
            from users.models import Friendship
            friends = Friendship.get_friends(self.request.user)
            friend_ids = [friend.id for friend in friends]
            
            # Ricette degli amici (tutte le visibilità eccetto private di altri)
            friends_recipes = queryset.filter(
                author__in=friend_ids
            ).exclude(
                visibility='private'
            )
            
            # Ricette pubbliche di tutti
            public_recipes = queryset.filter(visibility='public')
            
            # Ricette personali (tutte)
            my_recipes = queryset.filter(author=self.request.user)
            
            # Combina e ordina per popolarità (like - dislike)
            combined_ids = set()
            for recipe_set in [friends_recipes, public_recipes, my_recipes]:
                combined_ids.update(recipe_set.values_list('id', flat=True))
            
            queryset = queryset.filter(id__in=combined_ids)
        else:
            # Per utenti anonimi: solo ricette pubbliche
            queryset = queryset.filter(visibility='public')
        
        # Ordina per popolarità (numero di like - numero di dislike)
        return queryset.annotate(
            like_count=Count('likes'),
            dislike_count=Count('dislikes'),
            popularity=F('like_count') - F('dislike_count')
        ).order_by('-popularity', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Traduci timesince in italiano per ogni ricetta
        for recipe in context['recipes']:
            recipe.timesince_it = self.timesince_it(recipe.created_at)
        
        if self.request.user.is_authenticated:
            # Informazioni per utenti loggati
            from users.models import FriendRequest
            pending_requests = FriendRequest.objects.filter(
                to_user=self.request.user, 
                status='pending'
            ).count()
            context['pending_friend_requests'] = pending_requests
            
            # Statistiche per dashboard
            from users.models import Friendship
            
            total_recipes = Recipe.objects.filter(author=self.request.user).count()
            total_likes = Like.objects.filter(recipe__author=self.request.user).count()
            friends_count = Friendship.get_friends(self.request.user).count()
            
            context['user_stats'] = {
                'total_recipes': total_recipes,
                'total_likes': total_likes,
                'friends_count': friends_count,
            }
            
            # Ricette che l'utente ha già messo like
            user_likes = Like.objects.filter(user=self.request.user).values_list('recipe_id', flat=True)
            context['user_liked_recipes'] = list(user_likes)
            context['user_likes'] = list(user_likes)  # Compatibilità con il vecchio nome
        else:
            context['user_likes'] = []
            context['user_liked_recipes'] = []
        
        # Classifica temi più popolari (top tags)
        from django.db.models import Count
        popular_tags = []
        
        # Recupera tutti i tag dalle ricette visibili
        if self.request.user.is_authenticated:
            from users.models import Friendship
            friends = Friendship.get_friends(self.request.user)
            friend_ids = [f.id for f in friends]
            
            visible_recipes = models.Recipe.objects.exclude(
                visibility='private'
            ).exclude(
                Q(visibility='friends') & 
                ~Q(author__in=friend_ids) &
                ~Q(author=self.request.user)
            )
        else:
            visible_recipes = models.Recipe.objects.filter(visibility='public')
        
        # Estrai e conta i tag
        tag_counts = {}
        for recipe in visible_recipes:
            if recipe.tags:
                for tag in recipe.tags:
                    if tag:  # Ignora tag vuoti
                        tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Ordina per popolarità
        context['popular_tags'] = [ {'tag': tag, 'count': count} for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10] ]
        
        # Statistiche generali
        context['total_recipes'] = models.Recipe.objects.filter(visibility='public').count()
        context['total_users'] = User.objects.filter(userprofile__is_public=True).count()
        
        return context

class CommentForm(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Scrivi un commento...'}),
        }

@login_required
def add_comment(request, pk):
    recipe = get_object_or_404(models.Recipe, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.recipe = recipe
            comment.save()
            messages.success(request, 'Commento aggiunto!')
            return redirect('recipes-detail', pk=pk)
    else:
        form = CommentForm()
    return render(request, 'recipes/add_comment.html', {'form': form, 'recipe': recipe})

class RecipeDetailView(DetailView):
    model = models.Recipe
    template_name = 'recipes/recipe_detail.html'
  
class RecipeCreateView(LoginRequiredMixin, CreateView):
    model = models.Recipe
    fields = [
        'title', 'description', 'image', 'ingredients', 'instructions',
        'prep_time', 'cook_time', 'servings', 'difficulty', 'cuisine_type',
        'tags', 'personal_notes', 'visibility'
    ]
    template_name = 'recipes/recipe_form.html'
    success_url = reverse_lazy('recipes-home')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        # Conversione automatica dei tag
        tags_input = self.request.POST.get('tags')
        if tags_input:
            import json
            if tags_input.strip().startswith('['):
                # Se già JSON, usa così
                try:
                    tags = json.loads(tags_input)
                except Exception:
                    tags = []
            else:
                # Se stringa, separa per virgola
                tags = [t.strip() for t in tags_input.split(',') if t.strip()]
            form.instance.tags = tags
        return super().form_valid(form)

class RecipeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = models.Recipe
    fields = [
        'title', 'description', 'image', 'ingredients', 'instructions',
        'prep_time', 'cook_time', 'servings', 'difficulty', 'cuisine_type',
        'tags', 'personal_notes', 'visibility'
    ]
    template_name = 'recipes/recipe_form.html'

    def test_func(self):
        recipe = self.get_object()
        return self.request.user == recipe.author
           
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        # Conversione automatica dei tag
        tags_input = self.request.POST.get('tags')
        if tags_input:
            import json
            if tags_input.strip().startswith('['):
                try:
                    tags = json.loads(tags_input)
                except Exception:
                    tags = []
            else:
                tags = [t.strip() for t in tags_input.split(',') if t.strip()]
            form.instance.tags = tags
        return super().form_valid(form)
    
class RecipeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = models.Recipe
    success_url = reverse_lazy('recipes-home')  

    def test_func(self):
      recipe =  self.get_object()   
      return self.request.user == recipe.author

@login_required
@require_POST
def toggle_like(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    like, created = Like.objects.get_or_create(user=request.user, recipe=recipe)
    
    if not created:
        # Se il like già esiste, lo rimuoviamo (toggle)
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': recipe.likes.count(),
    })

