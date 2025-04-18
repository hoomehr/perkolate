from django.contrib import admin
from .models import Event, Target, Note, NoteVote

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'status', 'created_by')
    list_filter = ('status', 'start_date', 'created_by')
    search_fields = ('title', 'description')
    date_hierarchy = 'start_date'
    
@admin.register(Target)
class TargetAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'priority', 'due_date', 'assignee', 'created_by')
    list_filter = ('status', 'priority', 'due_date', 'assignee')
    search_fields = ('name', 'description')
    date_hierarchy = 'created_at'

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at', 'upvotes_count', 'downvotes_count')
    list_filter = ('created_at', 'created_by')
    search_fields = ('title', 'content')
    date_hierarchy = 'created_at'

@admin.register(NoteVote)
class NoteVoteAdmin(admin.ModelAdmin):
    list_display = ('note', 'user', 'vote_type', 'created_at')
    list_filter = ('vote_type', 'created_at')
    search_fields = ('note__title', 'user__username')
