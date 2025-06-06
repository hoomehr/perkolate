import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import models
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.events.models import Event, Target

def create_users():
    """Create sample users with different roles"""
    # Create or get admin user
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin.set_password('admin123')
    admin.save()
    
    # Create or get manager user
    manager, _ = User.objects.get_or_create(
        username='manager',
        defaults={
            'first_name': 'Manager',
            'last_name': 'User',
            'email': 'manager@example.com'
        }
    )
    manager.set_password('manager123')
    manager.save()
    
    # Create or get employee users
    employees = []
    for i in range(1, 4):
        employee, _ = User.objects.get_or_create(
            username=f'employee{i}',
            defaults={
                'first_name': f'Employee{i}',
                'last_name': 'User',
                'email': f'employee{i}@example.com'
            }
        )
        employee.set_password('employee123')
        employee.save()
        employees.append(employee)
    
    return admin, manager, employees

def create_events(users):
    """Create sample events"""
    admin, manager, employees = users
    
    # Clear existing events
    Event.objects.all().delete()
    
    # Sample event titles and descriptions
    event_data = [
        ('Team Building Workshop', 'A day of activities designed to improve team cohesion and communication.'),
        ('Quarterly Planning Session', 'Review Q2 results and plan for Q3 objectives.'),
        ('Product Launch Meeting', 'Final preparations for the new product launch.'),
        ('Customer Feedback Review', 'Analyze recent customer feedback and plan improvements.'),
        ('Tech Stack Evaluation', 'Evaluate current technologies and discuss potential upgrades.'),
        ('Annual Company Retreat', 'Company-wide planning and team building retreat.'),
        ('Sales Training Seminar', 'Training on new sales methodologies and tools.'),
        ('Marketing Campaign Kickoff', 'Kickoff meeting for the new marketing campaign.'),
    ]
    
    events = []
    now = timezone.now()
    
    for i, (title, description) in enumerate(event_data):
        # Vary the dates and creators of events
        days_offset = random.randint(-30, 60)
        start_date = now + timedelta(days=days_offset)
        end_date = start_date + timedelta(hours=random.randint(1, 8))
        
        # Select a creator
        if i < 2:
            creator = admin
        elif i < 5:
            creator = manager
        else:
            creator = random.choice(employees)
        
        # Select a status based on the date
        if days_offset < 0:
            status = 'completed'
        elif days_offset < 7:
            status = 'in_progress'
        else:
            status = 'planned'
        
        event = Event.objects.create(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            created_by=creator
        )
        events.append(event)
    
    return events

def create_targets(users):
    """Create sample targets"""
    admin, manager, employees = users
    
    # Clear existing targets
    Target.objects.all().delete()
    
    # Sample target names and descriptions
    target_data = [
        ('Increase Q3 Sales by 15%', 'Implement new sales strategies to boost quarterly sales.'),
        ('Reduce Customer Support Response Time', 'Achieve average first response time of under 2 hours.'),
        ('Launch Mobile App v2.0', 'Complete development and testing of the new mobile app version.'),
        ('Hire 3 New Developers', 'Complete recruitment process for expanding the development team.'),
        ('Improve Website Conversion Rate', 'Implement and test new website features to improve conversion.'),
        ('Complete Security Audit', 'Conduct comprehensive security audit of all systems.'),
        ('Redesign Marketing Materials', 'Update all marketing collateral with new branding.'),
        ('Implement New CRM System', 'Complete migration to the new customer relationship management system.'),
        ('Conduct Customer Satisfaction Survey', 'Prepare and distribute annual customer satisfaction survey.'),
        ('Optimize Supply Chain', 'Identify and implement improvements to the supply chain process.'),
    ]
    
    targets = []
    now = timezone.now().date()
    
    for i, (name, description) in enumerate(target_data):
        # Vary the dates, creators, assignees, and priorities
        days_offset = random.randint(-15, 45)
        due_date = now + timedelta(days=days_offset)
        
        # Select a creator
        if i < 3:
            creator = admin
        elif i < 7:
            creator = manager
        else:
            creator = random.choice(employees)
        
        # Select an assignee (sometimes None)
        if random.random() < 0.2:
            assignee = None
        else:
            assignee_options = employees + [manager]
            assignee = random.choice(assignee_options)
        
        # Select a status based on the date
        if days_offset < -7:
            status = 'completed'
        elif days_offset < 0:
            status = random.choice(['completed', 'blocked'])
        elif days_offset < 14:
            status = 'in_progress'
        else:
            status = 'not_started'
        
        # Select a priority
        priority = random.choice(['low', 'medium', 'medium', 'high', 'urgent'])
        
        target = Target.objects.create(
            name=name,
            description=description,
            status=status,
            priority=priority,
            due_date=due_date,
            assignee=assignee,
            created_by=creator
        )
        targets.append(target)
    
    return targets

def main():
    """Main function to seed the database"""
    print("Creating users...")
    users = create_users()
    
    print("Creating events...")
    events = create_events(users)
    
    print("Creating targets...")
    targets = create_targets(users)
    
    print(f"Database seeded successfully with:")
    print(f"- {User.objects.count()} users")
    print(f"- {Event.objects.count()} events")
    print(f"- {Target.objects.count()} targets")

if __name__ == "__main__":
    main() 