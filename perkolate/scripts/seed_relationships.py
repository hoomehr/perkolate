import os
import sys
import django
import random
from datetime import datetime, timedelta

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import models
from django.contrib.auth.models import User
from apps.events.models import Event, Target, Note

def create_relationships():
    """Create relationships between events, notes, and targets"""
    print("Creating relationships between events, notes, and targets...")
    
    # Get all existing objects
    events = list(Event.objects.all())
    targets = list(Target.objects.all())
    notes = list(Note.objects.all())
    
    if not events or not targets or not notes:
        print("Please run the main seed scripts first to create events, targets, and notes.")
        return
    
    # Create relationships for events
    print("Adding targets to events...")
    for event in events:
        # Add 1-3 random targets to each event
        num_targets = random.randint(1, 3)
        event_targets = random.sample(targets, min(num_targets, len(targets)))
        event.targets.add(*event_targets)
    
    # Create relationships for notes
    print("Adding events and targets to notes...")
    for note in notes:
        # Add 1-2 random events to each note
        num_events = random.randint(1, 2)
        note_events = random.sample(events, min(num_events, len(events)))
        note.events.add(*note_events)
        
        # Add a random target to 70% of notes
        if random.random() < 0.7:
            note.target = random.choice(targets)
            note.save()
    
    # Create relationships for targets
    print("Adding notes to targets...")
    for target in targets:
        # Add 1-3 random notes to each target
        num_notes = random.randint(1, 3)
        target_notes = random.sample(notes, min(num_notes, len(notes)))
        for note in target_notes:
            note.target = target
            note.save()
    
    print("Relationships created successfully!")
    print(f"- {Event.objects.count()} events with targets")
    print(f"- {Note.objects.count()} notes with events and targets")
    print(f"- {Target.objects.count()} targets with notes")

if __name__ == "__main__":
    create_relationships() 