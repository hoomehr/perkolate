from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from .models import Event, Target, Note, NoteVote, Comment
from .forms import EventForm, TargetForm, NoteForm
from datetime import datetime, date, timedelta
import json
from django.db.models import Q

User = get_user_model()

@login_required
def dashboard(request):
    """User dashboard with overview of recent items"""
    # Get recent events
    events = Event.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('-created_at')[:6]
    
    # Get active targets
    # For admin users, show all targets (limited to 6)
    # For regular users, only show their own targets and assigned targets
    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        targets = Target.objects.filter(
            ~Q(status='completed'),
            ~Q(status='cancelled')
        ).order_by('-created_at')[:6]
    else:
        targets = Target.objects.filter(
            Q(created_by=request.user) | Q(assignee=request.user),
            ~Q(status='completed'),
            ~Q(status='cancelled')
        ).order_by('-created_at')[:6]
    
    # Get recent notes
    notes = Note.objects.filter(
        Q(created_by=request.user) | Q(is_public=True)
    ).order_by('-created_at')[:6]
    
    # Get user votes for notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    context = {
        'events': events,
        'targets': targets,
        'notes': notes,
        'user_votes': user_votes,
    }
    
    return render(request, 'events/dashboard.html', context)

# Event Views
@login_required
def event_list(request):
    """Display a list of all events"""
    # For admin users, show all events
    # For regular users, only show their own events
    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        events = Event.objects.all()
        # Get featured events (3 most recent with images)
        featured_events = Event.objects.exclude(image='').order_by('-created_at')[:3]
    else:
        events = Event.objects.filter(created_by=request.user)
        # Get featured events (3 most recent with images created by user)
        featured_events = Event.objects.filter(created_by=request.user).exclude(image='').order_by('-created_at')[:3]
    
    # Set up pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'events/event_list.html', {
        'page_obj': page_obj,
        'featured_events': featured_events
    })

@login_required
def event_detail(request, pk):
    """Display details of a specific event"""
    event = get_object_or_404(Event, pk=pk)
    # Get all related notes ordered by creation date (newest first)
    notes = event.related_notes.all().order_by('-created_at')
    targets = event.targets.all()
    
    # Get user votes for notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    context = {
        'event': event,
        'notes': notes,
        'targets': targets,
        'user_votes': user_votes,
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def event_create(request):
    """Create a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'events/event_form.html', {'form': form, 'action': 'Create'})

@login_required
def event_update(request, pk):
    """Update an existing event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Only creator or admin can update
    if event.created_by != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('event_detail', pk=event.pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/event_form.html', {'form': form, 'event': event, 'action': 'Update'})

@login_required
def event_delete(request, pk):
    """Delete an event"""
    event = get_object_or_404(Event, pk=pk)
    
    # Only creator or admin can delete
    if event.created_by != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('event_detail', pk=event.pk)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('event_list')
    
    return render(request, 'events/event_confirm_delete.html', {'event': event})

# Target Views
@login_required
def target_list(request):
    """Display a list of all targets"""
    # For admin users, show all targets
    # For regular users, only show their own targets and assigned targets
    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        targets = Target.objects.all()
    else:
        targets = Target.objects.filter(assignee=request.user) | Target.objects.filter(created_by=request.user)
    
    # Set up pagination
    paginator = Paginator(targets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Check if there are any targets with due dates
    has_due_dates = any(target.due_date is not None for target in page_obj)
    
    # Get upcoming targets with due dates for the timeline
    upcoming_targets = Target.objects.filter(due_date__isnull=False).order_by('due_date')
    
    return render(request, 'events/target_list.html', {
        'page_obj': page_obj,
        'has_due_dates': has_due_dates,
        'upcoming_targets': upcoming_targets
    })

@login_required
def target_detail(request, pk):
    """Display details of a specific target"""
    target = get_object_or_404(Target, pk=pk)
    # Get all related notes ordered by creation date (newest first)
    notes = Note.objects.filter(target=target).order_by('-created_at')
    events = target.events.all()
    
    # Get user votes for notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    context = {
        'target': target,
        'notes': notes,
        'events': events,
        'user_votes': user_votes,
    }
    return render(request, 'events/target_detail.html', context)

@login_required
def target_create(request):
    """Create a new target"""
    if request.method == 'POST':
        form = TargetForm(request.POST)
        if form.is_valid():
            target = form.save(commit=False)
            target.created_by = request.user
            target.save()
            messages.success(request, 'Target created successfully!')
            return redirect('target_detail', pk=target.pk)
    else:
        form = TargetForm()
    
    return render(request, 'events/target_form.html', {'form': form, 'action': 'Create'})

@login_required
def target_update(request, pk):
    """Update an existing target"""
    target = get_object_or_404(Target, pk=pk)
    
    # Only creator, assignee or admin can update
    if target.created_by != request.user and target.assignee != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to edit this target.')
        return redirect('target_detail', pk=target.pk)
    
    if request.method == 'POST':
        form = TargetForm(request.POST, instance=target)
        if form.is_valid():
            form.save()
            messages.success(request, 'Target updated successfully!')
            return redirect('target_detail', pk=target.pk)
    else:
        form = TargetForm(instance=target)
    
    return render(request, 'events/target_form.html', {'form': form, 'target': target, 'action': 'Update'})

@login_required
def target_delete(request, pk):
    """Delete a target"""
    target = get_object_or_404(Target, pk=pk)
    
    # Only creator or admin can delete
    if target.created_by != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to delete this target.')
        return redirect('target_detail', pk=target.pk)
    
    if request.method == 'POST':
        target.delete()
        messages.success(request, 'Target deleted successfully!')
        return redirect('target_list')
    
    return render(request, 'events/target_confirm_delete.html', {'target': target})

# Note Views
@login_required
def note_board(request):
    """Display the notes board with all notes"""
    notes = Note.objects.all()
    
    # Instead of filtering by status (which doesn't exist in the model), 
    # we'll just provide all notes and let the frontend sort them
    notes_by_status = {
        'open': notes,  # In the template we'll use all notes
        'in_progress': [],
        'completed': [],
        'rejected': []
    }
    
    # Get all users for filtering
    users = User.objects.all()
    
    # Set up pagination
    paginator = Paginator(notes, 12)  # Show 12 notes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'events/note_board.html', {
        'page_obj': page_obj,
        'notes_by_status': notes_by_status,
        'users': users
    })

@login_required
def note_detail(request, pk):
    """Display details of a specific note"""
    note = get_object_or_404(Note, pk=pk)
    user_vote = None
    if request.user.is_authenticated:
        user_vote = NoteVote.objects.filter(note=note, user=request.user).first()
    
    context = {
        'note': note,
        'user_vote': user_vote,
        'related_events': note.events.all(),
        'target': note.target,
    }
    return render(request, 'events/note_detail.html', context)

@login_required
def note_create(request):
    """Create a new note"""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by = request.user
            note.save()
            # Save many-to-many relationships
            form.save_m2m()
            messages.success(request, 'Note posted successfully!')
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm()
    
    return render(request, 'events/note_form.html', {'form': form, 'action': 'Create'})

@login_required
def note_update(request, pk):
    """Update an existing note"""
    note = get_object_or_404(Note, pk=pk)
    
    # Only creator or admin can update
    if note.created_by != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to edit this note.')
        return redirect('note_detail', pk=note.pk)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note updated successfully!')
            return redirect('note_detail', pk=note.pk)
    else:
        form = NoteForm(instance=note)
    
    return render(request, 'events/note_form.html', {'form': form, 'note': note, 'action': 'Update'})

@login_required
def note_delete(request, pk):
    """Delete a note"""
    note = get_object_or_404(Note, pk=pk)
    
    # Only creator or admin can delete
    if note.created_by != request.user and not request.user.is_staff and not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        messages.error(request, 'You do not have permission to delete this note.')
        return redirect('note_detail', pk=note.pk)
    
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted successfully!')
        return redirect('note_board')
    
    return render(request, 'events/note_confirm_delete.html', {'note': note})

@login_required
def note_vote(request, pk):
    """Handle voting on a note"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=400)
    
    note = get_object_or_404(Note, pk=pk)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['upvote', 'downvote', 'remove']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    try:
        # Check if user already voted on this note
        existing_vote = NoteVote.objects.get(note=note, user=request.user)
        
        if vote_type == 'remove':
            # Remove the vote
            existing_vote.delete()
            return JsonResponse({
                'success': True,
                'message': 'Vote removed',
                'upvotes': note.upvotes_count,
                'downvotes': note.downvotes_count
            })
        elif existing_vote.vote_type != vote_type:
            # Change vote type
            existing_vote.vote_type = vote_type
            existing_vote.save()
            return JsonResponse({
                'success': True,
                'message': f'Changed to {vote_type}',
                'upvotes': note.upvotes_count,
                'downvotes': note.downvotes_count
            })
        else:
            # Same vote type, remove the vote
            existing_vote.delete()
            return JsonResponse({
                'success': True,
                'message': 'Vote removed',
                'upvotes': note.upvotes_count,
                'downvotes': note.downvotes_count
            })
            
    except NoteVote.DoesNotExist:
        # Create new vote
        if vote_type != 'remove':
            NoteVote.objects.create(
                note=note,
                user=request.user,
                vote_type=vote_type
            )
            return JsonResponse({
                'success': True,
                'message': f'Added {vote_type}',
                'upvotes': note.upvotes_count,
                'downvotes': note.downvotes_count
            })
    
    return JsonResponse({'error': 'Something went wrong'}, status=400)

# HTMX Views
@login_required
def htmx_event_list(request):
    """Return a partial HTML snippet of events for HTMX requests"""
    if not request.headers.get('HX-Request'):
        return redirect('event_list')  # Redirect if not an HTMX request
    
    # For admin users, show all events
    # For regular users, only show their own events
    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        events = Event.objects.all()
    else:
        events = Event.objects.filter(created_by=request.user)
    
    # Set up pagination
    paginator = Paginator(events, 5)  # Show 5 events per page for HTMX requests
    page_number = request.GET.get('page', 1)
    events = paginator.get_page(page_number)
    
    context = {'events': events, 'is_htmx': True}
    html = render_to_string('events/partials/event_list.html', context, request)
    return HttpResponse(html)

@login_required
def htmx_target_list(request):
    """Return a partial HTML snippet of targets for HTMX requests"""
    if not request.headers.get('HX-Request'):
        return redirect('target_list')  # Redirect if not an HTMX request
    
    # For admin users, show all targets
    # For regular users, only show their own targets and assigned targets
    if request.user.is_staff or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
        targets = Target.objects.all()
    else:
        targets = Target.objects.filter(assignee=request.user) | Target.objects.filter(created_by=request.user)
    
    # Set up pagination
    paginator = Paginator(targets, 5)  # Show 5 targets per page for HTMX requests
    page_number = request.GET.get('page', 1)
    targets = paginator.get_page(page_number)
    
    context = {'targets': targets, 'is_htmx': True}
    html = render_to_string('events/partials/target_list.html', context, request)
    return HttpResponse(html)

@login_required
def htmx_note_list(request):
    """Return a partial HTML snippet of notes for HTMX requests"""
    if not request.headers.get('HX-Request'):
        return redirect('note_board')  # Redirect if not an HTMX request
    
    notes = Note.objects.all()
    
    # Set up pagination
    paginator = Paginator(notes, 6)  # Show 6 notes per page for HTMX requests
    page_number = request.GET.get('page', 1)
    notes = paginator.get_page(page_number)
    
    context = {'notes': notes, 'is_htmx': True}
    html = render_to_string('events/partials/note_list.html', context, request)
    return HttpResponse(html)

@login_required
def htmx_vote_note(request, pk):
    """Handle voting on a note via HTMX"""
    if not request.headers.get('HX-Request') or request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    note = get_object_or_404(Note, pk=pk)
    vote_type = request.POST.get('vote_type')
    
    if vote_type not in ['upvote', 'downvote', 'remove']:
        return JsonResponse({'error': 'Invalid vote type'}, status=400)
    
    try:
        # Check if user already voted on this note
        existing_vote = NoteVote.objects.get(note=note, user=request.user)
        
        if vote_type == 'remove':
            # Remove the vote
            existing_vote.delete()
        elif existing_vote.vote_type != vote_type:
            # Change vote type
            existing_vote.vote_type = vote_type
            existing_vote.save()
        else:
            # Same vote type, remove the vote
            existing_vote.delete()
            
    except NoteVote.DoesNotExist:
        # Create new vote
        if vote_type != 'remove':
            NoteVote.objects.create(
                note=note,
                user=request.user,
                vote_type=vote_type
            )
    
    # Return updated counts
    context = {
        'note': note,
        'upvotes': note.upvotes_count,
        'downvotes': note.downvotes_count,
    }
    html = render_to_string('events/partials/vote_buttons.html', context, request)
    return HttpResponse(html)

@login_required
def htmx_note_upvote(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    user = request.user
    
    # Remove any existing downvote
    note.votes.filter(user=user, vote_type='downvote').delete()
    
    # Toggle upvote
    upvote = note.votes.filter(user=user, vote_type='upvote').first()
    if upvote:
        upvote.delete()
    else:
        NoteVote.objects.create(user=user, note=note, vote_type='upvote')
    
    # Get user votes for this note
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note=note, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    return render(request, 'events/partials/note_votes_update.html', {'note': note, 'user_votes': user_votes})

@login_required
def htmx_note_downvote(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    user = request.user
    
    # Remove any existing upvote
    note.votes.filter(user=user, vote_type='upvote').delete()
    
    # Toggle downvote
    downvote = note.votes.filter(user=user, vote_type='downvote').first()
    if downvote:
        downvote.delete()
    else:
        NoteVote.objects.create(user=user, note=note, vote_type='downvote')
    
    # Get user votes for this note
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note=note, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    return render(request, 'events/partials/note_votes_update.html', {'note': note, 'user_votes': user_votes})

@login_required
def htmx_add_comment(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == "POST":
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                note=note,
                user=request.user,
                content=content
            )
    return render(request, 'events/partials/note_comments.html', {'note': note})

@login_required
def htmx_get_notes(request, pk):
    """Get notes for an event via HTMX"""
    if not request.headers.get('HX-Request'):
        return redirect('event_detail', pk=pk)
    
    event = get_object_or_404(Event, pk=pk)
    notes = event.related_notes.all().order_by('-created_at')
    
    # Create a dictionary of user votes for these notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    context = {
        'event': event,
        'notes': notes,
        'user_votes': user_votes,
        'messages': messages.get_messages(request)
    }
    
    return render(request, 'events/partials/event_notes.html', context)

@login_required
def htmx_add_note(request, pk):
    """Add a note to an event or target via HTMX"""
    if not request.headers.get('HX-Request') or request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    content = request.POST.get('content')
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    
    # Try to get event or target
    try:
        event = Event.objects.get(pk=pk)
        target = None
        title = f"Note for {event.title}"
        template = 'events/partials/new_note.html'
    except Event.DoesNotExist:
        try:
            target = Target.objects.get(pk=pk)
            event = None
            title = f"Note for {target.name}"
            template = 'events/partials/new_note.html'
        except Target.DoesNotExist:
            return JsonResponse({'error': 'Event or target not found'}, status=404)
    
    # Create the note
    note = Note.objects.create(
        title=title,
        content=content,
        created_by=request.user,
        target=target  # Set target directly if it exists
    )
    
    # Add event association if it exists
    if event:
        note.events.add(event)
    
    # Get user votes for this note
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note=note, user=request.user)
        user_votes = {vote.note_id: vote.vote_type for vote in votes}
    
    # Add success message
    messages.success(request, 'Note added successfully!')
    
    # Return only the new note
    context = {
        'event': event,
        'target': target,
        'note': note,  # Pass single note instead of list
        'user_votes': user_votes,
        'is_new_note': True  # Flag to indicate this is a new note
    }
    
    # Render the message separately
    message_response = render(request, 'events/partials/messages.html', {'messages': messages.get_messages(request)})
    
    # Render the new note
    note_response = render(request, template, context)
    
    # Set headers to trigger message update and refresh notes list
    note_response['HX-Trigger'] = json.dumps({
        'showMessage': message_response.content.decode('utf-8')
    })
    
    return note_response

@login_required
def weekly_calendar(request):
    # Get date from request or use current date
    date_str = request.GET.get('date')
    if date_str:
        try:
            current_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            current_date = date.today()
    else:
        current_date = date.today()

    # Calculate the start of the week (Sunday)
    start_of_week = current_date - timedelta(days=current_date.weekday() + 1)
    if start_of_week.weekday() == 6:  # If today is Sunday
        start_of_week = current_date
    
    # Create a dictionary of days in the week
    days = {}
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        days[i] = day
    
    # Create a list of hours for the day
    hours = list(range(0, 24))
    
    context = {
        'days': days,
        'hours': hours,
    }
    
    return render(request, 'events/weekly_calendar.html', context)

# API endpoints for events
@login_required
def api_events(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filter events based on date range
    events_query = Event.objects.all().select_related('creator')
    
    if start_date and end_date:
        # Convert to datetime objects
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Filter events that overlap with the date range
        events_query = events_query.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        )
    
    # Process events for the calendar
    events_data = []
    for event in events_query:
        # Calculate position and height based on time
        start_time_obj = datetime.strptime(event.start_time.strftime('%H:%M'), '%H:%M').time()
        end_time_obj = datetime.strptime(event.end_time.strftime('%H:%M'), '%H:%M').time()
        
        # Convert time to pixels (1 hour = 60px)
        start_hour = start_time_obj.hour + start_time_obj.minute / 60
        end_hour = end_time_obj.hour + end_time_obj.minute / 60
        
        # Calculate the height based on duration
        height = (end_hour - start_hour) * 60
        
        # Handle multi-day events (simplified version)
        top_position = start_hour * 60
        
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'start_time': event.start_time.strftime('%H:%M'),
            'end_time': event.end_time.strftime('%H:%M'),
            'location': event.location,
            'creator': event.creator.username,
            'top_position': top_position,
            'height': max(height, 30),  # Minimum height of 30px for visibility
        })
    
    return JsonResponse({'events': events_data})

@login_required
def api_event_detail(request, pk):
    try:
        event = Event.objects.get(id=pk)
        
        # Gather participants if any
        participants = []
        # You would need a related model for participants
        # This is placeholder code:
        # for participant in event.participants.all():
        #     participants.append(participant.name)
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'start_date': event.start_date.strftime('%Y-%m-%d'),
            'end_date': event.end_date.strftime('%Y-%m-%d'),
            'start_time': event.start_time.strftime('%H:%M'),
            'end_time': event.end_time.strftime('%H:%M'),
            'location': event.location,
            'creator': event.creator.username,
            'participants': participants,
        }
        
        return JsonResponse(event_data)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)
