from django.db import models

# Create your models here.

class Todos(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    completed = models.BooleanField(default=False)
    def __str__(self):
        return self.title