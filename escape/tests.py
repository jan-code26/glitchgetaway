from django.test import TestCase
from django.urls import reverse

from .models import Room


class SmokeTests(TestCase):
    """Minimal smoke tests to verify key routes return expected status codes."""

    def setUp(self):
        self.room = Room.objects.create(
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
