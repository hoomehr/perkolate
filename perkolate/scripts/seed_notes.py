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
from apps.events.models import Note, NoteVote

def create_dummy_notes():
    """Create sample notes with random content"""
    
    # Get users to assign as creators and voters
    users = User.objects.all()
    if users.count() < 3:
        print("Not enough users in the database. Please run the main seed script first.")
        return
    
    # Clear existing notes and votes
    NoteVote.objects.all().delete()
    Note.objects.all().delete()
    
    # Sample note data
    note_data = [
        {
            "title": "Team Meeting Highlights",
            "content": "Today's team meeting covered several key points:\n\n1. Project Alpha is on track for delivery next month\n2. New client onboarding process has improved response times by 30%\n3. Office will be closed for maintenance next Friday\n4. Team building event planned for end of quarter\n\nPlease comment if you have any questions!"
        },
        {
            "title": "New Feature Suggestions",
            "content": "I've been thinking about some features that could improve our workflow:\n\n- Automated email notifications for task assignments\n- Integration with our calendar system\n- Mobile app version for field workers\n- Dark mode for the dashboard\n\nWhat do you all think? Any other suggestions?"
        },
        {
            "title": "Monthly Goals Update",
            "content": "Just a quick update on our monthly goals:\n\n✅ Increased customer satisfaction rating to 4.8/5\n✅ Completed training for all new team members\n⏳ Still working on reducing ticket response time\n❌ Did not meet new client acquisition target\n\nLet's focus on the remaining items for the next two weeks. Great work everyone!"
        },
        {
            "title": "Office Supply Requests",
            "content": "If anyone needs office supplies, please add them to the shared document by Thursday. I'll be placing an order on Friday morning.\n\nAlso, please remember to return any borrowed equipment to the supply closet when you're done with it."
        },
        {
            "title": "Tech Talk: New Library Overview",
            "content": "I'll be giving a brief tech talk next Tuesday at 3pm about the new data visualization library we're considering for the dashboard project. This should be useful for both the frontend and backend teams.\n\nThe talk will cover:\n- Basic usage examples\n- Performance considerations\n- Integration with our current stack\n\nHope to see you there!"
        },
        {
            "title": "Reminder: Timesheet Submissions",
            "content": "This is a friendly reminder that timesheets for this pay period are due tomorrow by 5pm. Please make sure to include all your hours and assign them to the correct projects.\n\nIf you have any questions or issues with the timesheet system, please let HR know as soon as possible."
        },
        {
            "title": "Brainstorming Session Results",
            "content": "Thanks to everyone who participated in yesterday's brainstorming session! We generated some excellent ideas for improving our customer portal.\n\nTop ideas (votes in parentheses):\n1. Customizable dashboard widgets (12)\n2. Integrated chat support (10)\n3. Document sharing capabilities (8)\n4. Visual progress tracking (7)\n\nThe product team will be reviewing these and following up next week."
        },
        {
            "title": "Upcoming System Maintenance",
            "content": "Please be advised that our servers will be undergoing scheduled maintenance this weekend from Saturday 10pm to Sunday 2am. During this time, the application will be unavailable.\n\nWe've chosen this timing to minimize disruption, but please plan accordingly if you need to access the system."
        },
        {
            "title": "Health and Wellness Tip",
            "content": "Remember to take regular breaks during your workday! The 20-20-20 rule is helpful for reducing eye strain: every 20 minutes, look at something 20 feet away for 20 seconds.\n\nAlso, don't forget about our company's wellness program benefits, including gym discounts and meditation app subscriptions."
        },
        {
            "title": "New Client Success Story",
            "content": "I wanted to share a success story from our recent project with Acme Corp. After implementing our solution, they've reported:\n\n- 40% reduction in processing time\n- 25% increase in customer satisfaction\n- 15% decrease in operational costs\n\nGreat work to everyone involved! This is exactly the kind of impact we strive to make."
        },
        {
            "title": "Coffee Machine Protocol",
            "content": "There seems to be some confusion about the coffee machine in the break room, so here's a quick guide:\n\n1. If you take the last cup, start a new pot\n2. Rinse your mug when you're done\n3. The left container is regular, right is decaf\n4. If you spill, please clean it up\n\nThank you for your cooperation in maintaining a clean break room for everyone!"
        },
        {
            "title": "Welcome to Our New Team Members",
            "content": "Please join me in welcoming Sarah and Michael to the development team! Sarah joins us as a frontend developer with experience in React, and Michael is our new DevOps engineer.\n\nThey'll be starting next Monday, so please take some time to introduce yourselves and help them get settled in."
        }
    ]
    
    print(f"Creating {len(note_data)} sample notes...")
    
    notes_created = []
    
    for i, note_info in enumerate(note_data):
        # Select a random creator
        creator = random.choice(users)
        
        # Create note with a timestamp within the last 30 days
        days_ago = random.randint(0, 30)
        created_at = datetime.now() - timedelta(days=days_ago, 
                                               hours=random.randint(0, 23), 
                                               minutes=random.randint(0, 59))
        
        note = Note.objects.create(
            title=note_info["title"],
            content=note_info["content"],
            created_by=creator,
            created_at=created_at,
            updated_at=created_at
        )
        
        notes_created.append(note)
        
    return notes_created

def create_dummy_votes(notes):
    """Create random votes for the notes"""
    
    users = User.objects.all()
    
    print("Adding random votes to notes...")
    votes_created = 0
    
    for note in notes:
        # Randomly determine how many users will vote on this note
        num_voters = random.randint(1, min(8, users.count()))
        
        # Randomly select users who will vote
        voters = random.sample(list(users), num_voters)
        
        for voter in voters:
            # Skip if voter is the note creator (optional)
            if voter == note.created_by and random.random() < 0.7:
                continue
                
            # Randomly choose upvote or downvote (biased toward upvotes)
            vote_type = 'upvote' if random.random() < 0.7 else 'downvote'
            
            # Create the vote
            NoteVote.objects.create(
                note=note,
                user=voter,
                vote_type=vote_type
            )
            
            votes_created += 1
    
    return votes_created

def main():
    """Main function to seed the database with notes"""
    notes = create_dummy_notes()
    votes_count = create_dummy_votes(notes)
    
    print(f"Successfully created {len(notes)} notes with {votes_count} votes!")

if __name__ == "__main__":
    main() 