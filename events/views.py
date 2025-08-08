# views.py
import os
import uuid
from django.core.files import File
from django.conf import settings
from reportlab.pdfgen import canvas
from .utils import generate_receipt_pdf
from django.http import FileResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Sum, F, Value as V
from django.db.models.functions import Coalesce
# Django & Core Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
# Custom User
from django.contrib.auth import get_user_model
User = get_user_model()

# Forms
from .forms import CustomUserCreationForm, RegistrationForm,EventForm, TicketForm

# Models
from .models import Category, Venue, Event, Ticket, Booking, Payment

# REST Framework
from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import BasePermission, SAFE_METHODS


# Serializers
from .serializers import (
    RegisterSerializer, UserSerializer,
    CategorySerializer, VenueSerializer,
    EventCreateSerializer, EventDetailSerializer,
    TicketSerializer, BookingSerializer, PaymentSerializer
)

# Custom Permissions
from .permissions import IsOrganizer
from django.contrib.auth import logout

# -------------------- API VIEWS --------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        user_data = self.get_serializer(user).data

        # Load user bookings with related ticket and event info
        bookings = Booking.objects.filter(user=user).select_related('ticket__event')
        booking_data = BookingSerializer(bookings, many=True).data

        return Response({
            'user': user_data,
            'bookings': booking_data
        })


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class VenueViewSet(viewsets.ModelViewSet):
    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return EventCreateSerializer
        return EventDetailSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class EventCreateView(generics.CreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventCreateSerializer
    permission_classes = [IsAuthenticated, IsOrganizer]


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(booking__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_organizer', False)

    def has_object_permission(self, request, view, obj):
        return obj.organizer == request.user
# -------------------- TEMPLATE VIEWS --------------------

def homepage_view(request):
    events = Event.objects.all().order_by('start_time')
    return render(request, 'events/home.html', {'events': events})



from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import Event, Ticket, Booking


def event_list_view(request):
    search = request.GET.get('q', '')
    filter_type = request.GET.get('status')  # No default to allow "All"
    now = timezone.now()

    # Base queryset
    events = Event.objects.all()

    # 🔍 Filter by search query
    if search:
        events = events.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(venue__name__icontains=search)
        )

    # 🔁 Filter by event status only if filter_type is set
    if filter_type == 'upcoming':
        events = events.filter(start_time__gt=now)
    elif filter_type == 'ongoing':
        events = events.filter(start_time__lte=now, end_time__gte=now)
    elif filter_type == 'ended':
        events = events.filter(end_time__lt=now)
    # else: no filtering = show all events

    # ⏳ Pagination
    paginator = Paginator(events.order_by('-start_time'), 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 🎟️ Add ticket/booking info per event
    event_data = []
    for event in page_obj:
        ticket = Ticket.objects.filter(event=event).first()
        total_booked = Booking.objects.filter(ticket=ticket).aggregate(total=Sum('quantity'))['total'] or 0
        remaining = (ticket.quantity - total_booked) if ticket else 0
        event_data.append({
            'event': event,
            'status': event.get_status(),
            'ticket': ticket,
            'total_booked': total_booked,
            'remaining': remaining
        })

    return render(request, 'events/event_list.html', {
        'search': search,
        'filter_type': filter_type,
        'page_obj': page_obj,
        'event_data': event_data
    })


def event_detail_view(request, pk):
    event = get_object_or_404(Event, pk=pk)
    search = request.GET.get('search', '')

    ticket = Ticket.objects.filter(event=event).first()
    status = event.get_status()
    allow_purchase = status == "Not started"

    if ticket:
        total_booked = Booking.objects.filter(ticket=ticket).aggregate(total=Sum('quantity'))['total'] or 0
        remaining = ticket.quantity - total_booked
    else:
        remaining = 0

    # Related Events
    other_events = Event.objects.exclude(pk=pk)
    if search:
        other_events = other_events.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    return render(request, 'events/event_detail.html', {
        'event': event,
        'status': status,
        'ticket': ticket,
        'remaining': remaining,
        'allow_purchase': allow_purchase,
        'other_events': other_events,
        'search': search,
    })

def login_view(request):
    from django.contrib.auth.forms import AuthenticationForm
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('event-list')
    return render(request, 'events/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Registration successful.')
            return redirect('login')  # or any other page
    else:
        form = RegistrationForm()
    return render(request, 'events/register.html', {'form': form})


@login_required
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(user=request.user).select_related('ticket__event', 'user', 'payment')

    return render(request, 'events/profile.html', {
        'user': user,
        'bookings': bookings
    })


@login_required
def cancel_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, "Booking canceled successfully.")
    return redirect('profile')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def organizer_dashboard_view(request):
    if not request.user.is_organizer:
        messages.error(request, "Access denied.")
        return redirect('event-list')
    
    events = Event.objects.filter(organizer=request.user)
    return render(request, 'events/organizer_dashboard.html', {'events': events})


@login_required
def create_event_view(request):
    default_categories = [
        'Music', 'Art', 'Sports', 'Tech', 'Business',
        'Health', 'Education', 'Food & Drink', 'Fashion', 'Comedy'
    ]
    for name in default_categories:
        Category.objects.get_or_create(name=name)
    default_venues = [
        'Bomas, Nairobi', 'KICC, Nairobi','Villa Rosa Kempinski, Nairobi','Hilton Hotel, Nairobi', 'The Alchemist, Nairobi',
        'Fairmont the Norfolk, Nairobi','Sarova Whitesands Beach Resort and Spa, Mombasa', 'Enashipai Resort and Spa, Naivasha', 'Lukenya Getaway'
    ]
    for name in default_venues:
        Venue.objects.get_or_create(name=name)
    if not request.user.is_organizer:
        messages.error(request, "Only organizers can create events.")
        return redirect('event-list')
    from .forms import EventForm
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, 'Event created successfully.')
            return redirect('create-ticket', event_id=event.id)
    else:
        form = EventForm()
    
    return render(request, 'events/create_event.html', {'form': form})


def edit_event_view(request, pk):
    event = get_object_or_404(Event, pk=pk, organizer=request.user)
    form = EventForm(request.POST or None, request.FILES or None, instance=event)
    if form.is_valid():
        form.save()
        messages.success(request, "Event updated.")
        return redirect('organizer-dashboard')
    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
def delete_event_view(request, pk):
    event = get_object_or_404(Event, pk=pk, organizer=request.user)
    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted.")
        return redirect('organizer-dashboard')
    return render(request, 'events/delete_event.html', {'event': event})


@login_required
def create_ticket_view(request, event_id):
    if not request.user.is_organizer:
        return redirect('event-list')

    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    ticket_types = ['regular', 'vip', 'student']
    forms = {}

    if request.method == 'POST':
        all_valid = True
        for t_type in ticket_types:
            form = TicketForm(request.POST, prefix=t_type)
            forms[t_type] = form
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.event = event
                ticket.ticket_type = t_type  # Force the ticket type
                ticket.save()
            else:
                all_valid = False

        if all_valid:
            return redirect('organizer-dashboard')
    else:
        for t_type in ticket_types:
            forms[t_type] = TicketForm(prefix=t_type)

    return render(request, 'events/create_ticket.html', {
        'forms': forms,
        'event': event
    })


@login_required
def view_event_bookings(request, event_id):
    event = get_object_or_404(Event, id=event_id, organizer=request.user)
    bookings = Booking.objects.filter(ticket__event=event).select_related('user', 'ticket')
    return render(request, 'events/event_bookings.html', {'bookings': bookings, 'event': event})






@login_required
def book_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    tickets = Ticket.objects.filter(event=event)

    if timezone.now() >= event.start_time:
        messages.error(request, "You cannot book tickets for events that have started or ended.")
        return redirect('event-detail', pk=event.id)

    if not tickets.exists():
        messages.error(request, "No tickets available for this event.")
        return redirect('event-detail', pk=event.id)

    if request.method == 'POST':
        if Booking.objects.filter(user=request.user, ticket__event=event).exists():
            messages.warning(request, "You have already booked this event.")
            return redirect('event-detail', pk=event.id)

        try:
                selected_ticket_id = int(request.POST.get('ticket_type'))
        except (TypeError, ValueError):
                messages.error(request, "Invalid ticket selection.")
                return redirect('book-event', event_id=event.id)

        quantity = int(request.POST.get('quantity', 1))
        method = request.POST.get('method', 'mpesa')

        ticket = get_object_or_404(Ticket, id=selected_ticket_id, event=event)

        total_booked = Booking.objects.filter(ticket=ticket).aggregate(total=Sum('quantity'))['total'] or 0
        remaining = ticket.quantity - total_booked

        if quantity > remaining:
            messages.error(request, f"Only {remaining} tickets remaining for {ticket.type}.")
            return redirect('book-event', event_id=event.id)

        total_price = ticket.price * quantity

        # Create booking
        booking = Booking.objects.create(
            user=request.user,
            ticket=ticket,
            quantity=quantity,
            payment_status='paid'
        )

        # Create payment
        transaction_id = str(uuid.uuid4())
        Payment.objects.create(
            booking=booking,
            amount=total_price,
            method=method,
            transaction_id=transaction_id,
            status='successful'
        )

        # Generate PDF receipt
        receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
        os.makedirs(receipts_dir, exist_ok=True)
        receipt_filename = f"receipt_{booking.id}.pdf"
        receipt_path = os.path.join(receipts_dir, receipt_filename)

        c = canvas.Canvas(receipt_path)
        c.drawString(100, 800, f"Receipt for Booking #{booking.id}")
        c.drawString(100, 780, f"Event: {event.title}")
        c.drawString(100, 760, f"User: {request.user.username}")
        c.drawString(100, 740, f"Ticket Type: {ticket.type}")
        c.drawString(100, 720, f"Quantity: {quantity}")
        c.drawString(100, 700, f"Total Paid: KES {total_price}")
        c.drawString(100, 680, f"Transaction ID: {transaction_id}")
        c.save()

        with open(receipt_path, 'rb') as f:
            booking.receipt_file.save(receipt_filename, File(f), save=True)

        messages.success(request, "Booking and payment successful.")
        return redirect('receipt', booking_id=booking.id)

    return render(request, 'events/book-event.html', {
        'event': event,
        'tickets': tickets,
    })

@login_required
def ticket_detail_view(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    event = ticket.event

    # All ticket types for this event (for the radio selection)
    all_tickets = Ticket.objects.filter(event=event)

    # Booking by the current user for this ticket
    booking = Booking.objects.filter(ticket=ticket, user=request.user).first()

    # Related payment (if booking exists)
    payment = Payment.objects.filter(booking=booking).first() if booking else None

    return render(request, 'events/ticket-detail.html', {
        'ticket': ticket,
        'all_tickets': all_tickets,
        'booking': booking,
        'payment': payment,
    })
@login_required
def receipt_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    payment = getattr(booking, 'payment', None)  # OneToOneField, can be None

    return render(request, 'events/receipt.html', {
        'booking': booking,
        'payment': payment,
    })



@login_required
def download_receipt_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if not booking.receipt_file:
        raise Http404("Receipt not found")

    receipt_path = booking.receipt_file.path
    if not os.path.exists(receipt_path):
        raise Http404("File does not exist")

    return FileResponse(open(receipt_path, 'rb'), as_attachment=True, filename=os.path.basename(receipt_path))









@login_required
def organizer_dashboard_view(request):
    # Get events by current organizer
    events = Event.objects.filter(organizer=request.user)

    # Prepare a list with enriched data
    dashboard_data = []

    for event in events:
        tickets = Ticket.objects.filter(event=event)
        event_data = {
            'event': event,
            'tickets_info': [],
            'total_revenue': 0,
        }

        for ticket in tickets:
            total_sold = Booking.objects.filter(ticket=ticket).aggregate(total=Coalesce(Sum('quantity'), V(0)))['total']
            revenue = total_sold * ticket.price
            event_data['tickets_info'].append({
                'type': ticket.type,
                'price': ticket.price,
                'total_sold': total_sold,
                'revenue': revenue,
            })
            event_data['total_revenue'] += revenue

        dashboard_data.append(event_data)

    return render(request, 'events/organizer_dashboard.html', {
        'dashboard_data': dashboard_data
    })