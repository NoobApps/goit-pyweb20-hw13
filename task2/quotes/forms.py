from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Author, Quote

class RegisterForm(UserCreationForm):
    pass

class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['fullname', 'born_date', 'born_location', 'description']

class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['quote', 'author', 'tags']
