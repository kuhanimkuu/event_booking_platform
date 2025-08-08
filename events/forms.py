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
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500',
            'placeholder': 'Email'
        })
    )

    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500',
                'placeholder': 'Username'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-pink-500 focus:border-pink-500',
                'placeholder': 'Password'
            }),
        }

from django.core.exceptions import ValidationError

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'category', 'venue', 'start_time', 'end_time', 'image']
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'w-full border border-pink-500 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-pink-400'
                }
            ),
            'end_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'w-full border border-pink-500 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-pink-400'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                continue  # Skip datetime fields already styled above
            field.widget.attrs.update({
                'class': 'w-full border border-pink-500 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-pink-400'
            })

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")

        return cleaned_data

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['name', 'type', 'price', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ✅ Replace the widget with a Select and reassign choices
        self.fields['type'].widget = forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
        })
        self.fields['type'].choices = Ticket.TICKET_TYPES

class BookingForm(forms.Form):
    ticket_type = forms.ChoiceField(label="Ticket Type", required=True)
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Enter quantity',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
        })
    )

    PAYMENT_METHOD_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        label="Payment Method",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
        })
    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        if event:
            # Populate ticket types related to the given event
            ticket_choices = [
                (ticket.id, f"{ticket.name} - KES {ticket.price} (Available: {ticket.remaining_quantity})")
                for ticket in Ticket.objects.filter(event=event)
            ]
            self.fields['ticket_type'].choices = ticket_choices
            self.fields['ticket_type'].widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-pink-500'
            })
            self.event = event  # Store for validation

    def clean(self):
        cleaned_data = super().clean()
        ticket_id = cleaned_data.get('ticket_type')
        quantity = cleaned_data.get('quantity')

        if ticket_id and quantity:
            try:
                ticket = Ticket.objects.get(id=ticket_id, event=self.event)
            except Ticket.DoesNotExist:
                raise forms.ValidationError("Selected ticket does not exist.")

            if quantity > ticket.remaining_quantity:
                raise forms.ValidationError(
                    f"Only {ticket.remaining_quantity} tickets available for {ticket.name}."
                )
        return cleaned_data