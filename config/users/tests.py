from django.test import TestCase, Client
class PublicProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_public = User.objects.create_user(username='publicuser', password='pass')
        self.user_private = User.objects.create_user(username='privateuser', password='pass')
        UserProfile.objects.create(user=self.user_public, is_public=True)
        UserProfile.objects.create(user=self.user_private, is_public=False)


    def test_public_profile_accessible(self):
        url = f'/users/{self.user_public.username}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_public.username)

    def test_private_profile_redirect(self):
        url = f'/users/{self.user_private.username}/'
        response = self.client.get(url, follow=True)
        # Dovrebbe reindirizzare alla home delle ricette (path '/')
        self.assertTrue(any(url == '/' for url, _ in response.redirect_chain))
        # Messaggio di avviso presente
        messages = list(response.context['messages'])
        self.assertTrue(any('privato' in str(m) for m in messages))

    def test_profile_access_as_authenticated_friend(self):
        # Un utente autenticato e amico può vedere il profilo privato
        friend = User.objects.create_user(username='friend', password='pass')
        UserProfile.objects.create(user=friend, is_public=True)
        # Crea amicizia
        Friendship.objects.create(user=friend, friend=self.user_private)
        Friendship.objects.create(user=self.user_private, friend=friend)
        self.client.login(username='friend', password='pass')
        url = f'/users/{self.user_private.username}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_private.username)
from django.contrib.auth.models import User
from .models import FriendRequest, Friendship, UserProfile
from django.core.exceptions import ValidationError

class FriendRequestModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')

    def test_unique_friend_request(self):
        # Si può creare una sola richiesta tra due utenti
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        with self.assertRaises(Exception):
            FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

    def test_accept_creates_friendship(self):
        req = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        req.accept()
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))

    def test_reject_does_not_create_friendship(self):
        req = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        req.reject()
        self.assertFalse(Friendship.are_friends(self.user1, self.user2))

    def test_cannot_accept_twice(self):
        req = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        req.accept()
        req.accept()  # Non deve creare duplicati
        friendships = Friendship.objects.filter(user=self.user1, friend=self.user2)
        self.assertEqual(friendships.count(), 1)

    def test_cannot_be_friend_with_self(self):
        # Non si può essere amici di se stessi
        with self.assertRaises(Exception):
            Friendship.objects.create(user=self.user1, friend=self.user1)

class FriendshipModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.user3 = User.objects.create_user(username='user3', password='pass')
        Friendship.objects.create(user=self.user1, friend=self.user2)
        Friendship.objects.create(user=self.user2, friend=self.user1)

    def test_are_friends(self):
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))
        self.assertFalse(Friendship.are_friends(self.user1, self.user3))

    def test_get_friends(self):
        friends = Friendship.get_friends(self.user1)
        self.assertIn(self.user2, friends)
        self.assertNotIn(self.user3, friends)

class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')

    def test_profile_is_created_once(self):
        # Un profilo per utente
        profile1 = UserProfile.objects.create(user=self.user1)
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=self.user1)

    def test_specialties_display(self):
        profile = UserProfile.objects.create(user=self.user1, cuisine_specialties=['italian', 'fusion'])
        display = profile.get_specialties_display()
        self.assertIn('Cucina Italiana', display)
        self.assertIn('Cucina Fusion', display)

class FriendRequestEdgeCaseTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')

    def test_reverse_friend_request(self):
        # Se esiste una richiesta da A->B, si può crearne una da B->A
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        req2 = FriendRequest.objects.create(from_user=self.user2, to_user=self.user1)
        self.assertEqual(req2.status, 'pending')

    def test_unique_together_enforced(self):
        # Unicità tra from_user e to_user
        FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        with self.assertRaises(Exception):
            FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)

    def test_accept_then_reject(self):
        req = FriendRequest.objects.create(from_user=self.user1, to_user=self.user2)
        req.accept()
        req.reject()
        self.assertEqual(req.status, 'rejected')
        self.assertTrue(Friendship.are_friends(self.user1, self.user2))

class FriendshipEdgeCaseTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass')
        self.user2 = User.objects.create_user(username='user2', password='pass')
        self.user3 = User.objects.create_user(username='user3', password='pass')

    def test_no_duplicate_friendship(self):
        Friendship.objects.create(user=self.user1, friend=self.user2)
        with self.assertRaises(ValidationError):
            Friendship(user=self.user1, friend=self.user1).save()

    def test_bidirectional_friendship(self):
        Friendship.objects.create(user=self.user1, friend=self.user2)
        Friendship.objects.create(user=self.user2, friend=self.user1)
        friends1 = Friendship.get_friends(self.user1)
        friends2 = Friendship.get_friends(self.user2)
        self.assertIn(self.user2, friends1)
        self.assertIn(self.user1, friends2)

    def test_get_friends_returns_queryset(self):
        Friendship.objects.create(user=self.user1, friend=self.user2)
        friends = Friendship.get_friends(self.user1)
        self.assertTrue(hasattr(friends, 'filter'))
        self.assertEqual(list(friends)[0], self.user2)
