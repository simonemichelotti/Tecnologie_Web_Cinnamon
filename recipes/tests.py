"""
Test suite per l'app recipes.

VISTA TESTATA CON CLIENT:
    RecipeListView (home page) — visibilità, autenticazione, contesto
    toggle_like — API-like endpoint, toggle behavior, autenticazione

Include test con:
    - Codici HTTP (200, 302, 405)
    - Contenuto della pagina
    - Logica di visibilità (public/friends/private)
    - Verifica del contesto (variabili template)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Recipe, Like, Comment
from users.models import UserProfile, Friendship


# =============================================================================
# TEST VISTA CON CLIENT: RecipeListView (Home page)
# =============================================================================

class RecipeListViewTest(TestCase):
    """Test della home page (RecipeListView) con Django test Client.

    La home ha logica complessa:
    - Anonimi vedono solo ricette pubbliche
    - Utenti loggati vedono: pubbliche + amici (non private) + proprie
    - Ricette ordinate per popolarità (like - dislike)
    """

    def setUp(self):
        self.client = Client()
        self.author = User.objects.create_user(username='chef', password='pass1234')
        self.viewer = User.objects.create_user(username='viewer', password='pass1234')
        UserProfile.objects.create(user=self.author, is_public=True)
        UserProfile.objects.create(user=self.viewer, is_public=True)

        # Ricetta pubblica
        self.public_recipe = Recipe.objects.create(
            title='Pasta Pubblica',
            description='Ricetta visibile a tutti',
            author=self.author,
            visibility='public'
        )
        # Ricetta solo amici
        self.friends_recipe = Recipe.objects.create(
            title='Pasta Segreta Amici',
            description='Solo per amici',
            author=self.author,
            visibility='friends'
        )
        # Ricetta privata
        self.private_recipe = Recipe.objects.create(
            title='Ricetta Super Privata',
            description='Solo per me',
            author=self.author,
            visibility='private'
        )

    # --- Codici HTTP ---

    def test_home_returns_200_anonymous(self):
        """La home è accessibile a utenti anonimi → 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_returns_200_authenticated(self):
        """La home è accessibile a utenti loggati → 200."""
        self.client.login(username='viewer', password='pass1234')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        """La home usa il template recipes/home.html."""
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'recipes/home.html')

    # --- Visibilità ricette per utenti anonimi ---

    def test_anonymous_sees_only_public_recipes(self):
        """Utenti anonimi vedono SOLO ricette pubbliche."""
        response = self.client.get('/')
        recipes = list(response.context['recipes'])
        recipe_titles = [r.title for r in recipes]
        self.assertIn('Pasta Pubblica', recipe_titles)
        self.assertNotIn('Pasta Segreta Amici', recipe_titles)
        self.assertNotIn('Ricetta Super Privata', recipe_titles)

    # --- Visibilità ricette per utenti autenticati ---

    def test_authenticated_sees_public_recipes(self):
        """Utente loggato vede ricette pubbliche (anche di non-amici)."""
        self.client.login(username='viewer', password='pass1234')
        response = self.client.get('/')
        recipe_titles = [r.title for r in response.context['recipes']]
        self.assertIn('Pasta Pubblica', recipe_titles)

    def test_authenticated_does_not_see_private_of_others(self):
        """Utente loggato NON vede ricette private di altri."""
        self.client.login(username='viewer', password='pass1234')
        response = self.client.get('/')
        recipe_titles = [r.title for r in response.context['recipes']]
        self.assertNotIn('Ricetta Super Privata', recipe_titles)

    def test_friend_sees_friends_only_recipes(self):
        """Un amico vede le ricette con visibilità 'friends'."""
        # Crea amicizia
        Friendship.objects.create(user=self.viewer, friend=self.author)
        Friendship.objects.create(user=self.author, friend=self.viewer)

        self.client.login(username='viewer', password='pass1234')
        response = self.client.get('/')
        recipe_titles = [r.title for r in response.context['recipes']]
        self.assertIn('Pasta Segreta Amici', recipe_titles)

    def test_non_friend_does_not_see_friends_only_recipes(self):
        """Un non-amico NON vede le ricette 'friends'."""
        self.client.login(username='viewer', password='pass1234')
        response = self.client.get('/')
        recipe_titles = [r.title for r in response.context['recipes']]
        self.assertNotIn('Pasta Segreta Amici', recipe_titles)

    def test_author_sees_own_private_recipes(self):
        """L'autore vede SEMPRE le proprie ricette, anche private."""
        self.client.login(username='chef', password='pass1234')
        response = self.client.get('/')
        recipe_titles = [r.title for r in response.context['recipes']]
        self.assertIn('Ricetta Super Privata', recipe_titles)
        self.assertIn('Pasta Segreta Amici', recipe_titles)
        self.assertIn('Pasta Pubblica', recipe_titles)

    # --- Contesto della pagina ---

    def test_context_contains_user_stats_for_authenticated(self):
        """Il contesto contiene le statistiche utente per utenti loggati."""
        self.client.login(username='chef', password='pass1234')
        response = self.client.get('/')
        self.assertIn('user_stats', response.context)
        stats = response.context['user_stats']
        self.assertIn('total_recipes', stats)
        self.assertIn('total_likes', stats)
        self.assertIn('friends_count', stats)

    def test_context_user_stats_correct_recipe_count(self):
        """Le statistiche mostrano il numero corretto di ricette dell'utente."""
        self.client.login(username='chef', password='pass1234')
        response = self.client.get('/')
        self.assertEqual(response.context['user_stats']['total_recipes'], 3)


# =============================================================================
# TEST VISTA CON CLIENT: toggle_like (API endpoint)
# =============================================================================

class ToggleLikeViewTest(TestCase):
    """Test dell'endpoint toggle_like — comportamento toggle, auth, metodo HTTP."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='liker', password='pass1234')
        UserProfile.objects.create(user=self.user, is_public=True)
        self.author = User.objects.create_user(username='chef', password='pass1234')
        self.recipe = Recipe.objects.create(
            title='Pasta Test',
            description='Test',
            author=self.author,
            visibility='public'
        )
        self.url = f'/recipe/{self.recipe.id}/like/'

    # --- Autenticazione ---

    def test_like_requires_authentication(self):
        """Utente anonimo → redirect a login (302)."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    # --- Metodo HTTP ---

    def test_like_rejects_get_request(self):
        """GET non è permesso → 405 Method Not Allowed."""
        self.client.login(username='liker', password='pass1234')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    # --- Comportamento toggle ---

    def test_first_like_creates_like(self):
        """Primo POST → crea il like, ritorna liked=True."""
        self.client.login(username='liker', password='pass1234')
        response = self.client.post(self.url)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['like_count'], 1)
        self.assertTrue(Like.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_second_like_removes_like(self):
        """Secondo POST → rimuove il like (toggle), ritorna liked=False."""
        self.client.login(username='liker', password='pass1234')
        self.client.post(self.url)  # Like
        response = self.client.post(self.url)  # Unlike
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['like_count'], 0)
        self.assertFalse(Like.objects.filter(user=self.user, recipe=self.recipe).exists())

    def test_toggle_like_returns_json(self):
        """La risposta è JSON con campi success, liked, like_count."""
        self.client.login(username='liker', password='pass1234')
        response = self.client.post(self.url)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertIn('success', data)
        self.assertIn('liked', data)
        self.assertIn('like_count', data)

    def test_like_nonexistent_recipe_returns_404(self):
        """Like su ricetta inesistente → 404."""
        self.client.login(username='liker', password='pass1234')
        response = self.client.post('/recipe/99999/like/')
        self.assertEqual(response.status_code, 404)
