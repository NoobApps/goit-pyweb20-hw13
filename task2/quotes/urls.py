from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import EmailAuthenticationForm

urlpatterns = [
    path('', views.home, name='home'),
    path('author/<int:pk>/', views.author_detail, name='author_detail'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='quotes/login.html',
        authentication_form=EmailAuthenticationForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('add-author/', views.add_author, name='add_author'),
    path('add-quote/', views.add_quote, name='add_quote'),

    # Скидання паролю
    path('reset-password/', 
         auth_views.PasswordResetView.as_view(
             template_name='quotes/password_reset.html',
             email_template_name='quotes/password_reset_email.html',
             subject_template_name='quotes/password_reset_subject.txt'
         ), 
         name='password_reset'),
         
    path('reset-password/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='quotes/password_reset_done.html'), 
         name='password_reset_done'),
         
    path('reset-password/confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='quotes/password_reset_confirm.html'), 
         name='password_reset_confirm'),
         
    path('reset-password/complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='quotes/password_reset_complete.html'), 
         name='password_reset_complete'),
]