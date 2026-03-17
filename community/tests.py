"""
Test suite per l'app community.

VISTA TESTATA CON CLIENT:
    CommunityDetailView — accesso a community pubblica/privata,
    permessi moderatore, controllo accesso basato su amicizia

Include test con:
    - Codici HTTP (200, redirect)
    - Contenuto della pagina
    - Logica di accesso (pubblica vs privata, membro vs non-membro)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Community, CommunityPost
from users.models import UserProfile, Friendship


# =============================================================================
# TEST VISTA CON CLIENT: CommunityDetailView
# =============================================================================

class CommunityDetailViewTest(TestCase):
    """Test della vista CommunityDetailView — accesso e permessi."""

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(username='creator', password='pass1234')
        self.member = User.objects.create_user(username='member', password='pass1234')
        self.outsider = User.objects.create_user(username='outsider', password='pass1234')
        self.friend_of_creator = User.objects.create_user(
            username='friend', password='pass1234'
        )
        UserProfile.objects.create(user=self.creator, is_public=True)
        UserProfile.objects.create(user=self.member, is_public=True)
        UserProfile.objects.create(user=self.outsider, is_public=True)
        UserProfile.objects.create(user=self.friend_of_creator, is_public=True)

        # Community pubblica
        self.public_community = Community.objects.create(
            name='Cucina Italiana',
            description='Community pubblica per tutti',
            creator=self.creator,
            visibility='public'
        )
        self.public_community.members.add(self.creator, self.member)
        self.public_community.moderators.add(self.creator)

        # Community privata
        self.private_community = Community.objects.create(
            name='Chef Segreti',
            description='Solo su invito',
            creator=self.creator,
            visibility='private'
        )
        self.private_community.members.add(self.creator, self.member)
        self.private_community.moderators.add(self.creator)

        # Amicizia creator-friend
        Friendship.objects.create(user=self.creator, friend=self.friend_of_creator)
        Friendship.objects.create(user=self.friend_of_creator, friend=self.creator)

    # --- Community pubblica ---

    def test_public_community_accessible_anonymous(self):
        """Community pubblica accessibile a utenti anonimi → 200."""
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_public_community_shows_name(self):
        """La pagina della community mostra il nome."""
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertContains(response, 'Cucina Italiana')

    def test_public_community_context_has_posts(self):
        """Il contesto contiene la lista dei post."""
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertIn('posts', response.context)

    # --- Community privata: accesso negato ---

    def test_private_community_denied_to_anonymous(self):
        """Community privata per utente anonimo → pagina di accesso negato (200 con template denied)."""
        response = self.client.get(f'/community/{self.private_community.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'community/private_community_denied.html')

    def test_private_community_denied_to_outsider(self):
        """Community privata per utente non-membro e non-amico → accesso negato."""
        self.client.login(username='outsider', password='pass1234')
        response = self.client.get(f'/community/{self.private_community.pk}/')
        self.assertTemplateUsed(response, 'community/private_community_denied.html')

    # --- Community privata: accesso consentito ---

    def test_private_community_accessible_to_member(self):
        """Un membro può accedere alla community privata → 200."""
        self.client.login(username='member', password='pass1234')
        response = self.client.get(f'/community/{self.private_community.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Chef Segreti')

    def test_private_community_accessible_to_creator(self):
        """Il creatore può accedere alla propria community privata → 200."""
        self.client.login(username='creator', password='pass1234')
        response = self.client.get(f'/community/{self.private_community.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_private_community_accessible_to_friend_of_creator(self):
        """Un amico del creatore può accedere alla community privata → 200."""
        self.client.login(username='friend', password='pass1234')
        response = self.client.get(f'/community/{self.private_community.pk}/')
        self.assertEqual(response.status_code, 200)

    # --- Contesto: stato membro/moderatore ---

    def test_context_is_member_true_for_member(self):
        """Il contesto mostra is_member=True per un membro."""
        self.client.login(username='member', password='pass1234')
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertTrue(response.context['is_member'])

    def test_context_is_member_false_for_outsider(self):
        """Il contesto mostra is_member=False per un non-membro."""
        self.client.login(username='outsider', password='pass1234')
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertFalse(response.context['is_member'])

    def test_context_is_moderator_true_for_creator(self):
        """Il contesto mostra is_moderator=True per il creatore."""
        self.client.login(username='creator', password='pass1234')
        response = self.client.get(f'/community/{self.public_community.pk}/')
        self.assertTrue(response.context['is_moderator'])

    # --- Community inesistente ---

    def test_nonexistent_community_returns_404(self):
        """Community inesistente → 404."""
        response = self.client.get('/community/99999/')
        self.assertEqual(response.status_code, 404)


# =============================================================================
# TEST VISTA CON CLIENT: join/leave community
# =============================================================================

class CommunityJoinLeaveTest(TestCase):
    """Test del join/leave community — verifica consistenza membership."""

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(username='creator', password='pass1234')
        self.user = User.objects.create_user(username='user', password='pass1234')
        UserProfile.objects.create(user=self.creator, is_public=True)
        UserProfile.objects.create(user=self.user, is_public=True)

        self.community = Community.objects.create(
            name='Test Community',
            description='Test',
            creator=self.creator,
            visibility='public'
        )
        self.community.members.add(self.creator)

    def test_join_adds_member(self):
        """POST su join aggiunge l'utente come membro."""
        self.client.login(username='user', password='pass1234')
        self.client.get(f'/community/{self.community.pk}/join/')
        self.assertTrue(self.community.members.filter(id=self.user.id).exists())

    def test_join_requires_login(self):
        """Join senza autenticazione → redirect a login."""
        response = self.client.get(f'/community/{self.community.pk}/join/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_leave_removes_member(self):
        """Leave rimuove l'utente dai membri."""
        self.community.members.add(self.user)
        self.client.login(username='user', password='pass1234')
        self.client.get(f'/community/{self.community.pk}/leave/')
        self.assertFalse(self.community.members.filter(id=self.user.id).exists())

    def test_join_idempotent(self):
        """Join chiamato due volte non crea duplicati."""
        self.client.login(username='user', password='pass1234')
        self.client.get(f'/community/{self.community.pk}/join/')
        self.client.get(f'/community/{self.community.pk}/join/')
        self.assertEqual(
            self.community.members.filter(id=self.user.id).count(), 1
        )

    def test_join_private_community_blocked(self):
        """Join diretto su community privata è bloccato → redirect senza aggiungere."""
        private = Community.objects.create(
            name='Privata', description='Test', creator=self.creator, visibility='private'
        )
        private.members.add(self.creator)

        self.client.login(username='user', password='pass1234')
        response = self.client.get(f'/community/{private.pk}/join/', follow=True)
        # L'utente NON deve essere stato aggiunto come membro
        self.assertFalse(private.members.filter(id=self.user.id).exists())
        # Deve mostrare messaggio di errore
        msgs = list(response.context['messages'])
        self.assertTrue(any('privata' in str(m).lower() for m in msgs))


# =============================================================================
# TEST VISTA CON CLIENT: CommunityListView — privacy community private
# =============================================================================

class CommunityListViewPrivacyTest(TestCase):
    """Test che la lista community nasconda le community private
    a chi non è amico del creatore, membro o moderatore."""

    def setUp(self):
        self.client = Client()
        self.creator = User.objects.create_user(username='creator', password='pass1234')
        self.friend = User.objects.create_user(username='friend', password='pass1234')
        self.member = User.objects.create_user(username='member', password='pass1234')
        self.outsider = User.objects.create_user(username='outsider', password='pass1234')
        UserProfile.objects.create(user=self.creator, is_public=True)
        UserProfile.objects.create(user=self.friend, is_public=True)
        UserProfile.objects.create(user=self.member, is_public=True)
        UserProfile.objects.create(user=self.outsider, is_public=True)

        # Community pubblica
        self.public_community = Community.objects.create(
            name='Pubblica', description='Aperta a tutti',
            creator=self.creator, visibility='public'
        )
        # Community privata
        self.private_community = Community.objects.create(
            name='Segreta', description='Solo amici e membri',
            creator=self.creator, visibility='private'
        )
        self.private_community.members.add(self.creator, self.member)

        # Amicizia creator <-> friend
        Friendship.objects.create(user=self.creator, friend=self.friend)
        Friendship.objects.create(user=self.friend, friend=self.creator)

    def test_anonymous_sees_only_public(self):
        """Utente anonimo vede solo le community pubbliche."""
        response = self.client.get('/community/')
        communities = list(response.context['communities'])
        self.assertIn(self.public_community, communities)
        self.assertNotIn(self.private_community, communities)

    def test_outsider_does_not_see_private(self):
        """Utente autenticato non-amico e non-membro non vede la community privata."""
        self.client.login(username='outsider', password='pass1234')
        response = self.client.get('/community/')
        communities = list(response.context['communities'])
        self.assertIn(self.public_community, communities)
        self.assertNotIn(self.private_community, communities)

    def test_friend_sees_private(self):
        """Amico del creatore vede la community privata nella lista."""
        self.client.login(username='friend', password='pass1234')
        response = self.client.get('/community/')
        communities = list(response.context['communities'])
        self.assertIn(self.private_community, communities)

    def test_member_sees_private(self):
        """Membro della community privata la vede nella lista."""
        self.client.login(username='member', password='pass1234')
        response = self.client.get('/community/')
        communities = list(response.context['communities'])
        self.assertIn(self.private_community, communities)

    def test_creator_sees_private(self):
        """Il creatore vede la propria community privata."""
        self.client.login(username='creator', password='pass1234')
        response = self.client.get('/community/')
        communities = list(response.context['communities'])
        self.assertIn(self.private_community, communities)

    def test_public_community_visible_to_all(self):
        """La community pubblica è sempre visibile: anonimo e autenticato."""
        # Anonimo
        response = self.client.get('/community/')
        self.assertIn(self.public_community, list(response.context['communities']))
        # Autenticato
        self.client.login(username='outsider', password='pass1234')
        response = self.client.get('/community/')
        self.assertIn(self.public_community, list(response.context['communities']))

