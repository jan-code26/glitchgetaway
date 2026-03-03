from django.test import TestCase
from django.urls import reverse

from .models import Room


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

