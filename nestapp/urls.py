# myapp/urls.py

from django.urls import path
from django.contrib.auth.views import LogoutView  # Import LogoutView from auth.views
from . import views  # Import your own views
from .views import upload_note_view , my_notes
from django.contrib.auth.views import LoginView


urlpatterns = [
    path('', views.landingpage, name='landingpage'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='landingpage'), name='logout'),
    path('upload/', upload_note_view, name='upload_note'),
    path('success/', views.success_page, name='success_page'),
    path('searchnotes/', views.search_notes_view, name='search_notes'),
    path('note/<int:note_id>/', views.view_note, name='view_note'),
    path('note/<int:note_id>/add/', views.add_to_my_notes, name='add_to_my_notes'),
    path('my_notes/', my_notes, name='my_notes'),
    path('note/<int:note_id>/upvote/', views.upvote_note, name='upvote_note'),
]
