from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django import forms
from .models import Event, Ticket
User = get_user_model()
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, widget=forms.Select)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'user_type']


class EventForm(forms.ModelForm):
     class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'venue', 'start_time', 'end_time', 'image']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'end_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
        }
        
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['name', 'type', 'price', 'quantity']


class BookingForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_METHOD_CHOICES, label="Payment Method")