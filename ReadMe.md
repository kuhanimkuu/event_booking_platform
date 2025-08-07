A Django-based web application that allows users to browse, book, and manage events. It supports user authentication, event creation (by organizers), ticket booking,and more.

## Features
- User registration, login, and logout
- Event listing and detailed views
- Ticket booking with quantity selection
- Payment simulation with method selection
- Automatic PDF receipt generation and download
- Receipt storage in user profile
- Organizer dashboard for managing events and tickets
- API endpoints (DRF) + HTML template views


## Tech
- Backend: Django, Django REST Framework
- Database: PostgreSQL (configurable)
- Media: Cloudinary (or local storage)
- PDF Generation: ReportLab
- Frontend: HTML, Tailwind CSS (via templates)
- Auth: Token (for APIs) and session-based (for templates)


## Installation
1. Clone the repo
bash
git clone https://github.com/kuhanimkuu/event_booking_platform.git

2. create a virtual environment
python -m venv .venv
source .venv/bin/activate  

3. install dependencies
pip install -r requirements.txt

4. setup environment variables
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=your-database-url
CLOUDINARY_URL=your-cloudinary-url

4. Apply migrations
python manage.py migrate

5. Create superuser
python manage.py createsuperuser

6. Start the server
 python manage.py runserver


## Authentication
API views: Token authentication
Template views: Session authentication

## Receipts
Linked to each booking and downloadable from the profile.

## Organizer Features
Create, edit, delete events
Manage tickets for each event
Organizer dashboard


Future Enhancements
    Email notifications with receipt
    Payment gateway integration (e.g. M-Pesa)
    Pagination and search for events
    Admin event approval flow
    Real-time ticket availability tracking