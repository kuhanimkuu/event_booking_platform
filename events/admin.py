from django.contrib import admin
from .models import User, Venue, Category, Event, Ticket, Booking, Payment
# Register your models here.
admin.site.register(User)
admin.site.register(Venue)
admin.site.register(Category)
admin.site.register(Event)
admin.site.register(Ticket)
admin.site.register(Booking)
admin.site.register(Payment)