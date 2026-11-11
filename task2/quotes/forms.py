from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Author, Quote

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label="Email адреса",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError("Користувач з таким Email вже існує.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email адреса",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['fullname', 'born_date', 'born_location', 'description']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'born_date': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'наприклад, November 07, 1867'}),
            'born_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'наприклад, Warsaw, Poland'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ['quote', 'author', 'tags']
        widgets = {
            'quote': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'author': forms.Select(attrs={'class': 'form-select'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'вкажіть теги через кому (наприклад: books, friends, quotes)'}),
        }