from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from .models import Event, Target, Note, NoteVote
from .forms import EventForm, TargetForm, NoteForm
from datetime import datetime, date, timedelta

User = get_user_model()

@login_required
def dashboard(request):
    """Main dashboard view showing events and targets"""
    events = Event.objects.all()
    targets = Target.objects.all()
    notes = Note.objects.all()[:3]  # Show only 3 most recent notes
    
    # For admin users, show all events/targets
    # For regular users, only show their own events and assigned targets
    if not request.user.is_staff and not hasattr(request.user, 'profile') and request.user.profile.role != 'admin':
        events = events.filter(created_by=request.user)
        targets = Target.objects.filter(assignee=request.user) | Target.objects.filter(created_by=request.user)
    
    context = {
        'events': events[:5],  # Show only 5 most recent events
        'targets': targets[:5],  # Show only 5 most recent targets
        'notes': notes,  # Show recent notes
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
    else:
        events = Event.objects.filter(created_by=request.user)
    
    # Set up pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'events/event_list.html', {'page_obj': page_obj})

@login_required
def event_detail(request, pk):
    """Display details of a specific event"""
    event = get_object_or_404(Event, pk=pk)
    return render(request, 'events/event_detail.html', {'event': event})

@login_required
def event_create(request):
    """Create a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST)
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
        form = EventForm(request.POST, instance=event)
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
    
    return render(request, 'events/target_list.html', {'page_obj': page_obj})

@login_required
def target_detail(request, pk):
    """Display details of a specific target"""
    target = get_object_or_404(Target, pk=pk)
    return render(request, 'events/target_detail.html', {'target': target})

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
        try:
            user_vote = NoteVote.objects.get(note=note, user=request.user).vote_type
        except NoteVote.DoesNotExist:
            pass
    
    return render(request, 'events/note_detail.html', {
        'note': note,
        'user_vote': user_vote
    })

@login_required
def note_create(request):
    """Create a new note"""
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.created_by = request.user
            note.save()
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
    note = get_object_or_404(Note, pk=note_id)
    
    # Check if user already has a vote
    try:
        vote = NoteVote.objects.get(note=note, user=request.user)
        
        if vote.vote_type == 'up':
            # User is un-upvoting
            vote.delete()
            user_vote = None
        else:
            # User is changing from down to up
            vote.vote_type = 'up'
            vote.save()
            user_vote = 'up'
    except NoteVote.DoesNotExist:
        # Create a new upvote
        NoteVote.objects.create(note=note, user=request.user, vote_type='up')
        user_vote = 'up'
    
    # Count votes
    upvotes = NoteVote.objects.filter(note=note, vote_type='up').count()
    downvotes = NoteVote.objects.filter(note=note, vote_type='down').count()
    
    context = {
        'note': note,
        'user_vote': user_vote,
        'upvotes': upvotes,
        'downvotes': downvotes
    }
    
    return render(request, 'events/partials/vote_buttons.html', context)

@login_required
def htmx_note_downvote(request, note_id):
    note = get_object_or_404(Note, pk=note_id)
    
    # Check if user already has a vote
    try:
        vote = NoteVote.objects.get(note=note, user=request.user)
        
        if vote.vote_type == 'down':
            # User is un-downvoting
            vote.delete()
            user_vote = None
        else:
            # User is changing from up to down
            vote.vote_type = 'down'
            vote.save()
            user_vote = 'down'
    except NoteVote.DoesNotExist:
        # Create a new downvote
        NoteVote.objects.create(note=note, user=request.user, vote_type='down')
        user_vote = 'down'
    
    # Count votes
    upvotes = NoteVote.objects.filter(note=note, vote_type='up').count()
    downvotes = NoteVote.objects.filter(note=note, vote_type='down').count()
    
    context = {
        'note': note,
        'user_vote': user_vote,
        'upvotes': upvotes,
        'downvotes': downvotes
    }
    
    return render(request, 'events/partials/vote_buttons.html', context)

@login_required
def htmx_add_note(request, pk):
    """Add a note to an event via HTMX"""
    if not request.headers.get('HX-Request') or request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    event = get_object_or_404(Event, pk=pk)
    content = request.POST.get('content')
    
    if not content:
        return JsonResponse({'error': 'Content is required'}, status=400)
    
    # Create the note
    note = Note.objects.create(
        title=f"Note for {event.title}",
        content=content,
        created_by=request.user,
        event=event
    )
    
    # Get all notes for this event
    notes = Note.objects.filter(event=event).order_by('-created_at')
    
    # Create a dictionary of user votes for these notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        for vote in votes:
            user_votes[vote.note.id] = vote
    
    context = {
        'event': event,
        'notes': notes,
        'user_votes': user_votes
    }
    
    return render(request, 'events/partials/event_notes.html', context)

@login_required
def htmx_get_notes(request, pk):
    """Get notes for an event via HTMX"""
    if not request.headers.get('HX-Request'):
        return redirect('event_detail', pk=pk)
    
    event = get_object_or_404(Event, pk=pk)
    notes = Note.objects.filter(event=event).order_by('-created_at')
    
    # Create a dictionary of user votes for these notes
    user_votes = {}
    if request.user.is_authenticated:
        votes = NoteVote.objects.filter(note__in=notes, user=request.user)
        for vote in votes:
            user_votes[vote.note.id] = vote
    
    context = {
        'event': event,
        'notes': notes,
        'user_votes': user_votes
    }
    
    return render(request, 'events/partials/event_notes.html', context)

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
