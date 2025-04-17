from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Event, Target, Note, NoteVote
from .forms import EventForm, TargetForm, NoteForm

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
    
    # Set up pagination
    paginator = Paginator(notes, 12)  # Show 12 notes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'events/note_board.html', {'page_obj': page_obj})

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
