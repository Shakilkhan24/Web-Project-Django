from django.db import models
from django.contrib.auth.models import User

class Task(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('working', 'Working on it'),
        ('stuck', 'Stuck'),
        ('done', 'Done')
    ]

    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    owner = models.EmailField()  # Assign tasks via email
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True, null=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    file = models.FileField(upload_to='task_files/', blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
