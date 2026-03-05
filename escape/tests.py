from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.management import call_command

from io import StringIO
from unittest.mock import patch

from .models import GameSession, GeneratedPuzzle, Room
from .services.puzzle_generation import generate_and_store_puzzles


class SmokeTests(TestCase):
    """Minimal smoke tests to verify key routes return expected status codes."""

    def setUp(self):
        self.room = Room.objects.create(
            order=1,
            title="Test Room",
            description="A test room",
            puzzle_question="What is 1+1?",
            puzzle_answer="2",
            hint="Think about basic arithmetic.",
        )

    def test_health_check(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok"})

    def test_portfolio_page(self):
        response = self.client.get(reverse("portfolio"))
        self.assertEqual(response.status_code, 200)

    def test_home_redirects_to_room(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("room"), fetch_redirect_response=False)

    def test_room_view_get(self):
        session = self.client.session
        session["current_room_id"] = self.room.id
        session.save()
        response = self.client.get(reverse("room"))
        self.assertEqual(response.status_code, 200)

    def test_room_view_correct_answer(self):
        session = self.client.session
        session["current_room_id"] = self.room.id
        session.save()
        response = self.client.post(reverse("room"), {"answer": "2"})
        # No next room → redirect to success
        self.assertRedirects(response, reverse("success"), fetch_redirect_response=False)

    def test_room_view_wrong_answer(self):
        session = self.client.session
        session["current_room_id"] = self.room.id
        session.save()
        response = self.client.post(reverse("room"), {"answer": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect")

    def test_success_view(self):
        response = self.client.get(reverse("success"))
        self.assertEqual(response.status_code, 200)


class AlternateAnswersTests(TestCase):
    """Tests for the multiple-accepted-answers feature."""

    def setUp(self):
        self.room = Room.objects.create(
            order=1,
            title="JS Room",
            description="JS puzzle",
            puzzle_question="Declare a variable in JS",
            puzzle_answer="var",
            alternate_answers="let, const",
            hint="var, let, or const all work.",
        )

    def test_primary_answer_accepted(self):
        self.assertTrue(self.room.is_answer_correct("var"))

    def test_alternate_answer_let_accepted(self):
        self.assertTrue(self.room.is_answer_correct("let"))

    def test_alternate_answer_const_accepted(self):
        self.assertTrue(self.room.is_answer_correct("const"))

    def test_wrong_answer_rejected(self):
        self.assertFalse(self.room.is_answer_correct("function"))

    def test_alternate_answer_case_insensitive(self):
        self.assertTrue(self.room.is_answer_correct("LET"))
        self.assertTrue(self.room.is_answer_correct("CONST"))

    def test_room_view_alternate_answer_redirects(self):
        """Submitting an alternate answer should advance to the next room (or success)."""
        session = self.client.session
        session["current_room_id"] = self.room.id
        session.save()
        response = self.client.post(reverse("room"), {"answer": "let"})
        self.assertRedirects(response, reverse("success"), fetch_redirect_response=False)


class RoomOrderingTests(TestCase):
    """Tests for explicit room ordering."""

    def setUp(self):
        self.room1 = Room.objects.create(order=1, title="Room A", description="A",
                                         puzzle_question="Q", puzzle_answer="a")
        self.room2 = Room.objects.create(order=2, title="Room B", description="B",
                                         puzzle_question="Q", puzzle_answer="b")

    def test_rooms_ordered_by_order_field(self):
        rooms = list(Room.objects.all())
        self.assertEqual(rooms[0], self.room1)
        self.assertEqual(rooms[1], self.room2)

    def test_correct_answer_advances_to_next_ordered_room(self):
        session = self.client.session
        session["current_room_id"] = self.room1.id
        session.save()
        self.client.post(reverse("room"), {"answer": "a"})
        session = self.client.session
        self.assertEqual(session["current_room_id"], self.room2.id)


class UserAuthTests(TestCase):
    """Tests for user registration, login, and logout."""

    def setUp(self):
        Room.objects.create(order=1, title="R", description="D",
                            puzzle_question="Q", puzzle_answer="a")

    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_redirects(self):
        response = self.client.post(reverse("register"),
                                    {"username": "newplayer", "password": "secret123"})
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertTrue(User.objects.filter(username="newplayer").exists())

    def test_register_duplicate_username_shows_error(self):
        User.objects.create_user(username="taken", password="x")
        response = self.client.post(reverse("register"),
                                    {"username": "taken", "password": "y"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already taken")

    def test_login_valid_credentials_redirects(self):
        User.objects.create_user(username="player1", password="pass1")
        response = self.client.post(reverse("login"),
                                    {"username": "player1", "password": "pass1"})
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_login_invalid_credentials_shows_error(self):
        response = self.client.post(reverse("login"),
                                    {"username": "nobody", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid credentials")

    def test_logout_redirects_to_portfolio(self):
        User.objects.create_user(username="p", password="p")
        self.client.login(username="p", password="p")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("portfolio"), fetch_redirect_response=False)

    def test_authenticated_user_redirected_away_from_register(self):
        User.objects.create_user(username="already", password="here")
        self.client.login(username="already", password="here")
        response = self.client.get(reverse("register"))
        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)


class GameSessionTests(TestCase):
    """Tests for GameSession creation and finalisation."""

    def setUp(self):
        self.room = Room.objects.create(order=1, title="T", description="D",
                                        puzzle_question="Q", puzzle_answer="ans")

    def test_game_session_created_on_home(self):
        self.client.get(reverse("home"))
        self.assertEqual(GameSession.objects.count(), 1)

    def test_game_session_linked_to_user(self):
        user = User.objects.create_user(username="gamer", password="pw")
        self.client.login(username="gamer", password="pw")
        self.client.get(reverse("home"))
        gs = GameSession.objects.first()
        self.assertEqual(gs.user, user)
        self.assertEqual(gs.display_name, "gamer")

    def test_wrong_answer_increments_total_attempts(self):
        self.client.get(reverse("home"))
        gs = GameSession.objects.first()
        session = self.client.session
        session["current_room_id"] = self.room.id
        session.save()
        self.client.post(reverse("room"), {"answer": "wrong"})
        gs.refresh_from_db()
        self.assertEqual(gs.total_attempts, 1)

    def test_success_finalises_game_session(self):
        self.client.get(reverse("home"))
        gs = GameSession.objects.first()
        session = self.client.session
        session["current_room_id"] = self.room.id
        session["game_session_id"] = gs.id
        session.save()
        self.client.post(reverse("room"), {"answer": "ans"})
        self.client.get(reverse("success"))
        gs.refresh_from_db()
        self.assertTrue(gs.completed)
        self.assertIsNotNone(gs.finished_at)

    def test_elapsed_display_format(self):
        gs = GameSession(
            started_at=timezone.now() - timezone.timedelta(seconds=125),
            finished_at=timezone.now(),
            completed=True,
        )
        # elapsed ≈ 125 s → 02:05
        self.assertEqual(gs.elapsed_display, "02:05")

    def test_elapsed_display_none_when_not_finished(self):
        gs = GameSession(started_at=timezone.now(), completed=False)
        self.assertEqual(gs.elapsed_display, "--:--")


class LeaderboardTests(TestCase):
    """Tests for the leaderboard view."""

    def setUp(self):
        Room.objects.create(order=1, title="R", description="D",
                            puzzle_question="Q", puzzle_answer="a")

    def _make_session(self, name, elapsed_secs, attempts=0):
        start = timezone.now() - timezone.timedelta(seconds=elapsed_secs)
        return GameSession.objects.create(
            display_name=name,
            started_at=start,
            finished_at=timezone.now(),
            total_attempts=attempts,
            completed=True,
        )

    def test_leaderboard_page_loads(self):
        response = self.client.get(reverse("leaderboard"))
        self.assertEqual(response.status_code, 200)

    def test_leaderboard_shows_completed_sessions(self):
        self._make_session("alice", 60)
        self._make_session("bob", 90)
        response = self.client.get(reverse("leaderboard"))
        self.assertContains(response, "alice")
        self.assertContains(response, "bob")

    def test_leaderboard_ordered_fastest_first(self):
        self._make_session("slow", 300)
        self._make_session("fast", 30)
        response = self.client.get(reverse("leaderboard"))
        content = response.content.decode()
        self.assertLess(content.index("fast"), content.index("slow"))

    def test_leaderboard_command_in_room_redirects(self):
        session = self.client.session
        room = Room.objects.first()
        session["current_room_id"] = room.id
        session.save()
        response = self.client.post(reverse("room"), {"answer": "leaderboard"})
        self.assertRedirects(response, reverse("leaderboard"), fetch_redirect_response=False)

    def test_success_view_shows_rank(self):
        self._make_session("other", 30)  # faster player already in board
        room = Room.objects.first()
        self.client.get(reverse("home"))
        gs = GameSession.objects.latest('id')
        session = self.client.session
        session["current_room_id"] = room.id
        session["game_session_id"] = gs.id
        session.save()
        self.client.post(reverse("room"), {"answer": "a"})
        response = self.client.get(reverse("success"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rank")


class PuzzleGenerationServiceTests(TestCase):
    def _mock_puzzles(self):
        return [{
            'title': 'Binary Search Gate',
            'description': 'Find the missing midpoint token.',
            'puzzle_question': 'What is the midpoint index for 0..8?',
            'puzzle_answer': '4',
            'alternate_answers': 'four',
            'hint': 'Use integer division.',
        }]

    @patch('escape.services.puzzle_generation.get_provider')
    def test_generate_and_store_auto_approves_to_room(self, mock_get_provider):
        class FakeProvider:
            def generate_puzzles(self, topic=None, count=5, custom_prompt=None):
                return self._puzzles

        fake_provider = FakeProvider()
        fake_provider._puzzles = self._mock_puzzles()
        mock_get_provider.return_value = fake_provider

        result = generate_and_store_puzzles(
            topic='algorithms',
            count=1,
            auto_approve=True,
        )

        self.assertEqual(result['created_count'], 1)
        self.assertEqual(result['approved_count'], 1)
        self.assertEqual(result['duplicate_skipped_count'], 0)
        self.assertEqual(Room.objects.count(), 1)
        self.assertEqual(GeneratedPuzzle.objects.count(), 1)
        self.assertEqual(
            GeneratedPuzzle.objects.first().status,
            GeneratedPuzzle.STATUS_APPROVED,
        )

    @patch('escape.services.puzzle_generation.get_provider')
    def test_generate_and_store_skips_invalid_payload(self, mock_get_provider):
        class FakeProvider:
            def generate_puzzles(self, topic=None, count=5, custom_prompt=None):
                return [{'title': 'Missing required keys'}]

        mock_get_provider.return_value = FakeProvider()
        result = generate_and_store_puzzles(count=1)

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(result['skipped_count'], 1)
        self.assertEqual(result['duplicate_skipped_count'], 0)
        self.assertEqual(GeneratedPuzzle.objects.count(), 0)

    @patch('escape.services.puzzle_generation.get_provider')
    def test_generate_and_store_prevents_duplicate_room_on_auto_approve(self, mock_get_provider):
        class FakeProvider:
            def generate_puzzles(self, topic=None, count=5, custom_prompt=None):
                return [{
                    'title': 'Binary Search Gate',
                    'description': 'Find the missing midpoint token.',
                    'puzzle_question': 'What is the midpoint index for 0..8?',
                    'puzzle_answer': '4',
                    'alternate_answers': 'four',
                    'hint': 'Use integer division.',
                }]

        Room.objects.create(
            order=1,
            title='Binary Search Gate',
            description='Existing room',
            puzzle_question='What is the midpoint index for 0..8?',
            puzzle_answer='4',
        )
        mock_get_provider.return_value = FakeProvider()

        result = generate_and_store_puzzles(count=1, auto_approve=True)

        self.assertEqual(result['created_count'], 0)
        self.assertEqual(result['approved_count'], 0)
        self.assertEqual(result['skipped_count'], 1)
        self.assertEqual(result['duplicate_skipped_count'], 1)
        self.assertIn('duplicate live room exists', result['errors'][0])
        self.assertEqual(Room.objects.count(), 1)
        self.assertEqual(GeneratedPuzzle.objects.count(), 0)


class AdminGeneratePuzzlesViewTests(TestCase):
    def test_admin_generate_redirects_without_session(self):
        response = self.client.get(reverse('admin_generate_puzzles'))
        self.assertRedirects(response, reverse('admin_terminal'), fetch_redirect_response=False)

    def test_admin_generate_page_loads_with_admin_session(self):
        session = self.client.session
        session['is_admin'] = True
        session.save()

        response = self.client.get(reverse('admin_generate_puzzles'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate AI Puzzles')

    @patch('escape.views.generate_and_store_puzzles')
    def test_admin_generate_posts_with_auto_approve(self, mock_generate):
        session = self.client.session
        session['is_admin'] = True
        session.save()

        mock_generate.return_value = {
            'provider_type': 'OpenAI',
            'generated_count': 1,
            'created_count': 1,
            'approved_count': 1,
            'skipped_count': 0,
            'duplicate_skipped_count': 0,
            'errors': [],
        }

        response = self.client.post(reverse('admin_generate_puzzles'), {
            'topic': 'css',
            'count': '1',
            'provider': 'openai',
            'prompt': '',
            'confirm_live_publish': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auto-approved 1 puzzle')
        self.assertContains(response, '[[ GENERATION SUMMARY ]]')
        self.assertContains(response, 'Completed with no issues.')
        self.assertContains(response, 'Review Generated Puzzles')
        mock_generate.assert_called_once()
        self.assertTrue(mock_generate.call_args.kwargs['auto_approve'])

    @patch('escape.views.generate_and_store_puzzles')
    def test_admin_generate_shows_duplicate_prevention_banner(self, mock_generate):
        session = self.client.session
        session['is_admin'] = True
        session.save()

        mock_generate.return_value = {
            'provider_type': 'OpenAI',
            'generated_count': 2,
            'created_count': 1,
            'approved_count': 1,
            'skipped_count': 1,
            'duplicate_skipped_count': 1,
            'errors': ['Puzzle #2: duplicate live room exists for this title/question'],
        }

        response = self.client.post(reverse('admin_generate_puzzles'), {
            'topic': 'css',
            'count': '2',
            'provider': 'openai',
            'prompt': '',
            'confirm_live_publish': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prevented 1 duplicate live publish.')
        self.assertContains(response, 'Completed with warnings. Review details below.')
        self.assertContains(response, 'Show Details')
        self.assertContains(response, 'duplicate live room exists for this title/question')

    @patch('escape.views.generate_and_store_puzzles')
    def test_admin_generate_requires_publish_confirmation(self, mock_generate):
        session = self.client.session
        session['is_admin'] = True
        session.save()

        response = self.client.post(reverse('admin_generate_puzzles'), {
            'topic': 'css',
            'count': '1',
            'provider': 'openai',
            'prompt': '',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Confirm live publish before generating auto-approved puzzles.')
        mock_generate.assert_not_called()


class GeneratePuzzlesCommandTests(TestCase):
    @patch('escape.management.commands.generate_puzzles.generate_and_store_puzzles')
    def test_command_uses_shared_service(self, mock_generate):
        mock_generate.return_value = {
            'provider_type': 'Anthropic',
            'generated_count': 1,
            'created_count': 1,
            'approved_count': 0,
            'skipped_count': 0,
            'errors': [],
        }

        out = StringIO()
        call_command('generate_puzzles', topic='http', count=1, stdout=out)

        self.assertIn('Successfully generated 1 puzzle', out.getvalue())
        mock_generate.assert_called_once()
        self.assertFalse(mock_generate.call_args.kwargs['auto_approve'])

