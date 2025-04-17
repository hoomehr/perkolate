# Perkolate

Perkolate is a web-based event and task management application built with Django. It allows users to create, track, and manage events and targets, as well as share notes with team members.

## Features

- **User Authentication**: Login, registration, and role-based access control
- **Event Management**: Create, view, update, and delete events
- **Target Tracking**: Set and track targets with priorities, statuses, and assignees
- **Notes Board**: Share notes with team members with upvote/downvote functionality
- **Dashboard**: View recent events, targets, and notes at a glance

## Technology Stack

- Django 4.2
- PostgreSQL
- Bootstrap 5
- Font Awesome
- JavaScript (for interactive components)

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/perkolate.git
   cd perkolate
   ```

2. Create a virtual environment:
   ```
   python -m venv perkolate_env
   source perkolate_env/bin/activate  # On Windows, use: perkolate_env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   DATABASE_NAME=perkolate
   DATABASE_USER=postgres
   DATABASE_PASSWORD=postgres
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   ```

5. Set up the database:
   ```
   python perkolate/manage.py migrate
   ```

6. Create a superuser:
   ```
   python perkolate/manage.py createsuperuser
   ```

7. Seed the database with sample data:
   ```
   python perkolate/scripts/seed_data.py
   python perkolate/scripts/seed_notes.py
   ```

8. Run the server:
   ```
   python perkolate/manage.py runserver
   ```

9. Access the application at `http://localhost:8000/`

## User Roles

- **Admin**: Can view, create, update, and delete all events, targets, and notes
- **Manager**: Can create events and targets, assign targets to employees
- **Employee**: Can create events, update assigned targets, and create/vote on notes

## License

This project is licensed under the MIT License - see the LICENSE file for details. 