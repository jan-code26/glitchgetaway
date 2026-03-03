from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from unittest.mock import patch, MagicMock

from .models import GameSession, GeneratedPuzzle, Room


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


# ── AI puzzle generation tests ──────────────────────────────────────────────

SAMPLE_PUZZLES = [
    {
        "order": 1,
        "title": "Hello World",
        "description": "A classic puzzle.",
        "puzzle_question": "What does print('hello') output?",
        "puzzle_answer": "hello",
        "alternate_answers": "",
        "hint": "It prints what's in the quotes.",
    }
]


class GeneratedPuzzleModelTests(TestCase):
    """Tests for the GeneratedPuzzle model."""

    def _make_puzzle(self, **kwargs):
        defaults = dict(
            order=1,
            title="Test Puzzle",
            description="A test.",
            puzzle_question="Q?",
            puzzle_answer="a",
        )
        defaults.update(kwargs)
        return GeneratedPuzzle.objects.create(**defaults)

    def test_default_status_is_pending(self):
        gp = self._make_puzzle()
        self.assertEqual(gp.status, GeneratedPuzzle.STATUS_PENDING)

    def test_str_includes_status_and_title(self):
        gp = self._make_puzzle(title="My Puzzle")
        self.assertIn("Pending", str(gp))
        self.assertIn("My Puzzle", str(gp))

    def test_ordering_newest_first(self):
        gp1 = self._make_puzzle(title="First")
        gp2 = self._make_puzzle(title="Second")
        puzzles = list(GeneratedPuzzle.objects.all())
        self.assertEqual(puzzles[0], gp2)
        self.assertEqual(puzzles[1], gp1)


class GeneratePuzzlesServiceTests(TestCase):
    """Unit tests for escape.services.generate_puzzles_from_ai."""

    def test_raises_when_api_key_missing(self):
        from escape.services import generate_puzzles_from_ai
        with self.settings(ANTHROPIC_API_KEY=''):
            with self.assertRaises(RuntimeError):
                generate_puzzles_from_ai(count=1)

    @patch('escape.services.anthropic')
    def test_valid_response_returns_puzzle_list(self, mock_anthropic_module):
        import json
        from escape.services import generate_puzzles_from_ai

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(SAMPLE_PUZZLES))]
        mock_client.messages.create.return_value = mock_message

        with self.settings(ANTHROPIC_API_KEY='test-key'):
            result = generate_puzzles_from_ai(count=1)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['puzzle_answer'], 'hello')

    @patch('escape.services.anthropic')
    def test_invalid_json_raises_runtime_error(self, mock_anthropic_module):
        from escape.services import generate_puzzles_from_ai

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="not json at all")]
        mock_client.messages.create.return_value = mock_message

        with self.settings(ANTHROPIC_API_KEY='test-key'):
            with self.assertRaises(RuntimeError):
                generate_puzzles_from_ai(count=1)


class GeneratePuzzlesCommandTests(TestCase):
    """Tests for the generate_puzzles management command."""

    @patch('escape.services.anthropic')
    def test_command_creates_pending_puzzles(self, mock_anthropic_module):
        import json
        from django.core.management import call_command
        from io import StringIO

        mock_client = MagicMock()
        mock_anthropic_module.Anthropic.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text=json.dumps(SAMPLE_PUZZLES))]
        mock_client.messages.create.return_value = mock_message

        out = StringIO()
        with self.settings(ANTHROPIC_API_KEY='test-key'):
            call_command('generate_puzzles', '--count', '1', stdout=out)

        self.assertEqual(GeneratedPuzzle.objects.count(), 1)
        gp = GeneratedPuzzle.objects.first()
        self.assertEqual(gp.status, GeneratedPuzzle.STATUS_PENDING)
        self.assertIn("1 GeneratedPuzzle", out.getvalue())

    @patch('escape.services.anthropic')
    def test_command_error_when_api_key_missing(self, _mock):
        from django.core.management import call_command
        from django.core.management.base import CommandError

        with self.settings(ANTHROPIC_API_KEY=''):
            with self.assertRaises(CommandError):
                call_command('generate_puzzles', '--count', '1')


class AdminApproveRejectTests(TestCase):
    """Tests for the approve/reject admin actions on GeneratedPuzzle."""

    def setUp(self):
        self.superuser = User.objects.create_superuser('admin', 'a@a.com', 'pass')
        self.client.login(username='admin', password='pass')
        self.gp = GeneratedPuzzle.objects.create(
            order=1,
            title="AI Puzzle",
            description="desc",
            puzzle_question="Q?",
            puzzle_answer="ans",
            hint="hint",
        )

    def test_approve_action_creates_room(self):
        data = {
            'action': 'approve_puzzles',
            '_selected_action': [self.gp.pk],
        }
        self.client.post(
            '/admin/escape/generatedpuzzle/',
            data,
            follow=True,
        )
        self.gp.refresh_from_db()
        self.assertEqual(self.gp.status, GeneratedPuzzle.STATUS_APPROVED)
        self.assertTrue(Room.objects.filter(title="AI Puzzle").exists())

    def test_reject_action_marks_rejected(self):
        data = {
            'action': 'reject_puzzles',
            '_selected_action': [self.gp.pk],
        }
        self.client.post(
            '/admin/escape/generatedpuzzle/',
            data,
            follow=True,
        )
        self.gp.refresh_from_db()
        self.assertEqual(self.gp.status, GeneratedPuzzle.STATUS_REJECTED)
        self.assertFalse(Room.objects.filter(title="AI Puzzle").exists())

