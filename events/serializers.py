from rest_framework import serializers
from .models import  User, Category, Venue, Event, Ticket, Booking, Payment
from django.contrib.auth.password_validation import validate_password
from django.db.models import Sum
# User registration serializer
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password'],
            user_type=validated_data.get('user_type', 'attendee')
        )
        return user


# User serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_organizer']


#Category serializer
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


# Venue serializer
class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ['id', 'name', 'address', 'capacity']


# Ticket serializer

class TicketSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_start_time = serializers.DateTimeField(source='event.start_time', read_only=True)
    event_end_time = serializers.DateTimeField(source='event.end_time', read_only=True)
    available_quantity = serializers.SerializerMethodField()
    is_sold_out = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'event', 'event_title', 'event_start_time', 'event_end_time',
            'name', 'price', 'quantity', 'available_quantity', 'is_sold_out'
        ]

    def get_available_quantity(self, ticket):
        from .models import Booking  # Avoid circular imports
        booked = Booking.objects.filter(ticket=ticket).aggregate(total=Sum('quantity'))['total'] or 0
        return ticket.quantity - booked

    def get_is_sold_out(self, ticket):
        return self.get_available_quantity(ticket) <= 0

# Event serializer(Read)
class EventDetailSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    category = CategorySerializer()
    venue = VenueSerializer()
    tickets = TicketSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'category', 'venue',
            'organizer', 'start_time', 'end_time', 'image',
            'created_at', 'tickets'
        ]
    def get_available_tickets(self, obj):
        booked = Booking.objects.filter(ticket=obj).aggregate(total=Sum('quantity'))['total'] or 0
        return obj.quantity - booked


# Event serializer (write)
class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'venue',
            'start_time', 'end_time', 'image'
        ]

# Booking serializer
from django.db.models import Sum
from rest_framework import serializers
from .models import Booking, Ticket

from rest_framework import serializers
from django.db.models import Sum
from .models import Booking, Ticket

class BookingSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    ticket = TicketSerializer(read_only=True)
    ticket_id = serializers.PrimaryKeyRelatedField(
        queryset=Ticket.objects.all(), source='ticket', write_only=True
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'ticket', 'ticket_id',
            'quantity', 'booked_at', 'payment_status'
        ]
        read_only_fields = ['booked_at', 'payment_status']

    def validate(self, attrs):
        ticket = attrs['ticket']
        requested_qty = attrs['quantity']
        booked = Booking.objects.filter(ticket=ticket).aggregate(total=Sum('quantity'))['total'] or 0
        available = ticket.quantity - booked

        if requested_qty > available:
            raise serializers.ValidationError(
                f"Only {available} ticket(s) available for '{ticket.name}'."
            )
        return attrs

    def create(self, validated_data):
        # Attach the currently authenticated user
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# Payment serializer
class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)
    booking_id = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.all(), source='booking', write_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id', 'booking', 'booking_id',
            'amount', 'method', 'transaction_id',
            'status', 'created_at'
        ]
        read_only_fields = ['created_at']

