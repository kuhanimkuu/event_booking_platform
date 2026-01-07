A Django-based web application that allows users to browse, book, and manage events. It supports user authentication, event creation (by organizers), ticket booking,and more.

## Live Demo

**[Live Project Link]**  

*Apologies for the inconvenience — the previous hosting link on Render is no longer active. The live version will be hosted on a new platform shortly.*



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
Role-based access control for organizers and users

## Receipts
Linked to each booking and downloadable from the profile.

## Organizer Features
Create, edit, delete events
Manage tickets for each event
Organizer dashboard with event analytics
Automatic ticket availability tracking

## API Endpoints
Full CRUD for events, tickets, and bookings
User profile management
Token-based authentication for API requests
Adapters built for Stripe and Amadeus (integration in progress)


## Frontend
HTML templates with Tailwind CSS
Responsive design for desktop, tablet, and mobile
Dynamic pages for events, bookings, and profiles


## Future Enhancements
Email notifications with receipt
Full payment gateway integration (Stripe, M-Pesa)
Integration with Amadeus API for flight and travel bookings
Pagination and search for events
Admin event approval flow
Real-time ticket availability tracking
Deployment to a stable production host outside of Render