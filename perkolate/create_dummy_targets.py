from django.contrib.auth.models import User
from apps.events.models import Target

def create_dummy_targets():
    # Check if there are existing targets
    existing_count = Target.objects.count()
    print(f'Current target count: {existing_count}')

    # Only create if there are fewer than 5 targets
    if existing_count < 5:
        # Get or create a user to assign targets to
        user, created = User.objects.get_or_create(username='admin', defaults={'is_staff': True, 'is_superuser': True})
        if created:
            user.set_password('admin')
            user.save()
            print(f'Created admin user: {user.username}')
        else:
            print(f'Using existing user: {user.username}')
        
        # Create dummy targets with different statuses and priorities
        targets_data = [
            {
                'name': 'Complete Project Documentation',
                'description': 'Finalize all documentation for the Q3 release including API references and user guides.',
                'status': 'in_progress',
                'priority': 'high',
                'due_date': '2025-05-15',
            },
            {
                'name': 'Implement User Authentication',
                'description': 'Add secure login and registration with email verification.',
                'status': 'not_started',
                'priority': 'urgent',
                'due_date': '2025-04-30',
            },
            {
                'name': 'Mobile App UI Design',
                'description': 'Create wireframes and mockups for the new mobile application interface.',
                'status': 'in_progress',
                'priority': 'medium',
                'due_date': '2025-05-10',
            },
            {
                'name': 'Database Optimization',
                'description': 'Improve query performance and add missing indexes for the production database.',
                'status': 'not_started',
                'priority': 'low',
                'due_date': '2025-06-01',
            },
            {
                'name': 'Client Meeting Preparation',
                'description': 'Prepare slides and demos for the upcoming client presentation.',
                'status': 'in_progress',
                'priority': 'high',
                'due_date': '2025-04-25',
            }
        ]
        
        for data in targets_data:
            target, created = Target.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'status': data['status'],
                    'priority': data['priority'],
                    'due_date': data['due_date'],
                    'created_by': user,
                    'assignee': user
                }
            )
            if created:
                print(f'Created target: {target.name}')
            else:
                print(f'Target already exists: {target.name}')
    else:
        print('Skipping target creation - already have sufficient targets')

if __name__ == '__main__':
    create_dummy_targets() 