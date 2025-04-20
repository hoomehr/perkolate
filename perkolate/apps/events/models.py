from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Event(models.Model):
    """Model for events in the system"""
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    targets = models.ManyToManyField('Target', related_name='events', blank=True)
    image = models.ImageField(upload_to='event_images/', blank=True, null=True, help_text="Featured image for the event (recommended ratio 2:3)")
    is_public = models.BooleanField(default=True, help_text="If checked, all users can see this event")

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-start_date']


class Target(models.Model):
    """Model for targets in the system"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_targets'
    )
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_targets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['due_date', '-priority']


class Note(models.Model):
    """Model for notes/posts in the system"""
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    events = models.ManyToManyField(Event, related_name='related_notes', blank=True)
    target = models.ForeignKey('Target', on_delete=models.SET_NULL, related_name='notes', null=True, blank=True)
    is_public = models.BooleanField(default=True, help_text="If checked, all users can see this note")
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
    @property
    def upvotes_count(self):
        return self.votes.filter(vote_type='upvote').count()
    
    @property
    def downvotes_count(self):
        return self.votes.filter(vote_type='downvote').count()


class NoteVote(models.Model):
    """Model for votes on notes"""
    
    VOTE_CHOICES = [
        ('upvote', 'Upvote'),
        ('downvote', 'Downvote'),
    ]
    
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='note_votes')
    vote_type = models.CharField(max_length=10, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('note', 'user')
        ordering = ['-created_at']


class Comment(models.Model):
    """Model for comments on notes"""
    
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='note_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.note.title}"
    
    class Meta:
        ordering = ['-created_at']
