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
