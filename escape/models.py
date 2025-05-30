from django.db import models

# Create your models here.

class Room(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    puzzle_question = models.TextField()
    puzzle_answer = models.CharField(max_length=100)
    hint = models.TextField(blank=True, default="No hint available.")

    def __str__(self):
        return self.title
