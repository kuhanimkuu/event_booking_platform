from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from django.utils import timezone
import os
from django.conf import settings
# Create your models here.

# User model
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('attendee', 'Attendee'),
        ('organizer', 'Organizer'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='attendee')

    def is_organizer(self):
        return self.user_type == 'organizer'
    

# Venue model
class Venue(models.Model):
    name = models.CharField(max_length=255)
  
    def __str__(self):
        return self.name
    

# Category model
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# Event model
class Event(models.Model):
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    venue = models.ForeignKey(Venue, on_delete=models.SET_NULL, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    image = CloudinaryField('image', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    

# Ticket model
class Ticket(models.Model):
    TICKET_TYPES = [
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('early_bird', 'Early Bird'),
        ('student', 'Student'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TICKET_TYPES, default='regular')  # New field
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

# Booking model
class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    booked_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], default='pending')
    receipt_file = models.FileField(upload_to='receipts/', null=True, blank=True) 
    def __str__(self):
        return f"{self.user.username} - {self.ticket.event.title}"
    

# Payment model
class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=50)  # e.g., 'mpesa', 'stripe', 'paypal'
    transaction_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=[
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"


