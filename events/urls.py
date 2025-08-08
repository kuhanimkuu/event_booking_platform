from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, CustomAuthToken, UserProfileView,
    EventViewSet, VenueViewSet, TicketViewSet, BookingViewSet
)
from . import views as template_views

# DRF router for API viewsets
router = DefaultRouter()
router.register(r'events', EventViewSet, basename='event')
router.register(r'venues', VenueViewSet, basename='venue')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'bookings', BookingViewSet, basename='booking')

# API routes (all under /api/)
api_urlpatterns = [
    path('register/', RegisterView.as_view(), name='api-register'),
    path('login/', CustomAuthToken.as_view(), name='api-login'),
    path('profile/', UserProfileView.as_view(), name='api-profile'),
    path('', include(router.urls)),
]

# Template-based (HTML) routes
template_urlpatterns = [
    # Public
    path('',template_views.homepage_view, name='Home'), 
    path('events/events', template_views.event_list_view, name='event-list'),
    path('events/<int:pk>/', template_views.event_detail_view, name='event-detail'),

    # Auth
    path('login/', template_views.login_view, name='login'),
    path('logout/', template_views.logout_view, name='logout'),
    path('register/', template_views.register_view, name='register'),
    path('profile/', template_views.profile_view, name='profile'),

    # Booking
    path('events/<int:event_id>/book/', template_views.book_event_view, name='book-event'),
    path('bookings/<int:pk>/cancel/', template_views.cancel_booking_view, name='cancel-booking'),
    path('events/<int:event_id>/', template_views.event_detail_view, name='event-detail'),
    path('receipt/<int:booking_id>/', template_views.receipt_view, name='receipt'),
    path('tickets/<int:pk>/', template_views.ticket_detail_view, name='ticket-detail'),
    path('receipt/<int:booking_id>/download/', template_views.download_receipt_view, name='download-receipt'),
    # Organizer Dashboard
    path('organizer/dashboard/', template_views.organizer_dashboard_view, name='organizer-dashboard'),

    # Organizer Event CRUD
    path('organizer/events/create/', template_views.create_event_view, name='create-event'),
    path('organizer/events/<int:pk>/edit/', template_views.edit_event_view, name='edit-event'),
    path('organizer/events/<int:pk>/delete/', template_views.delete_event_view, name='delete-event'),

    # Organizer Ticket CRUD
    path('organizer/events/<int:event_id>/tickets/create/', template_views.create_ticket_view, name='create-ticket'),
    
]

# Final combined URL patterns
urlpatterns = [
    path('api/', include(api_urlpatterns)),
] + template_urlpatterns
