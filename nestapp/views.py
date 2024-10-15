from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import SignupForm, NoteUploadForm, CommentForm, PrintOrderForm
from .models import Note, MyNotes, Upvote, Order
from PyPDF2 import PdfReader

from django.core.files.storage import FileSystemStorage
from .models import Note , MyNotes ,  Upvote
import time  # Import the time module for generating timestamps
###
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Note, MyNotes, Upvote, Comment  # Import Comment model
from .forms import CommentForm  # Import CommentForm
from django.shortcuts import render
from django.contrib import messages

from datetime import datetime
from cloudinary import uploader  # Import the uploader module


def landingpage(request):
    return render(request, 'index.html')

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landingpage')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')

@login_required
def upload_note_view(request):
    if request.method == 'POST':
        form = NoteUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            note = form.save(commit=False)  # Create the note instance but don't save yet
            note.uploaded_by = request.user  # Set the user who uploaded the note

            # Check if a file is uploaded
            uploaded_file = request.FILES.get('file')  # Get the uploaded file
            
            if uploaded_file:  # Check if the file exists
                try:
                    # Upload the file to Cloudinary
                    cloudinary_response = uploader.upload(uploaded_file , resource_type="raw")
                    
                    # Save the URL of the uploaded file to your model
                    note.file = cloudinary_response['secure_url']  # Save the Cloudinary URL to the note

                except Exception as e:
                    # Handle any errors that occur during the upload
                    print(f"Error uploading to Cloudinary: {e}")
                    return render(request, 'upload_note.html', {
                        'form': form,
                        'error': 'There was an error uploading your file. Please try again.'
                    })

            note.save()  # Save the note instance after uploading the file
            
            return redirect('success_page')  # Redirect to a success page
        else:
            # Handle form errors
            print(form.errors)
    else:
        form = NoteUploadForm()
        
    return render(request, 'upload_note.html', {'form': form})

def success_page(request):
    return render(request, 'success_page.html')

def search_notes_view(request):
    branches = ['CSE', 'ECE', 'ME']  # Replace with actual branches
    semesters = range(1, 9)  # Assuming 8 semesters

    keyword = request.GET.get('keyword', '')
    branch = request.GET.get('branch', '')
    semester = request.GET.get('semester', '')

    # Filter the notes based on the search criteria
    notes = Note.objects.filter(is_approved=True)

    if keyword:
        notes = notes.filter(subject__icontains=keyword)

    if branch:
        notes = notes.filter(branch=branch)

    if semester:
        notes = notes.filter(semester=int(semester))

    # Generate a single timestamp for cache-busting
    timestamp = int(time.time())

    # Iterate over each note to add `pdf_url` and `timestamp`
    for note in notes:
        # Ensure that the `file` field returns the correct URL
        # If `file` is a Cloudinary URL, it might already be a string
        # Otherwise, use `note.file.url` if `file` is a FileField/ImageField
        note.pdf_url = note.file if isinstance(note.file, str) else note.file.url
        note.timestamp = timestamp

    # Pass the notes and other filters to the context
    context = {
        'notes': notes,
        'branches': branches,
        'semesters': semesters,
        'keyword': keyword,
    }

    return render(request, 'search_notes.html', context)

@login_required
def view_note(request, note_id):
    note = get_object_or_404(Note, id=note_id, is_approved=True)
    
    # Check if the user has already added this note to "My Notes"
    added_to_my_notes = note in request.user.notes.all()
    upvote_count = note.upvote_set.count()
    has_upvoted = note.upvote_set.filter(user=request.user).exists() if request.user.is_authenticated else False

    # The PDF URL is the Cloudinary URL from the note's file field
    pdf_url = note.file  # Assuming 'file' already holds the Cloudinary URL

    # Handle comment form submission
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.note = note
            comment.user = request.user
            comment.save()
            return redirect('view_note', note_id=note.id)
    else:
        comment_form = CommentForm()

    # Retrieve comments for the current note
    comments = note.comments.filter(is_approved=True)

    context = {
        'note': note,
        'added_to_my_notes': added_to_my_notes,
        'pdf_url': pdf_url,
        'upvote_count': upvote_count,
        'has_upvoted': has_upvoted,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'view_note.html', context)

@login_required
def add_to_my_notes(request, note_id):
    note = get_object_or_404(Note, id=note_id, is_approved=True)
    user = request.user

    # Check if the note is already added to "My Notes"
    if not MyNotes.objects.filter(user=user, note=note).exists():
        MyNotes.objects.create(user=user, note=note)  # Add to My Notes
        print("Note added to My Notes")
    else:
        print("Note already in My Notes")

    # Redirect back to the view_note page after adding the note
    return redirect('view_note', note_id=note.id)


@login_required
def my_notes(request):
    notes = MyNotes.objects.filter(user=request.user)
    return render(request, 'my_notes.html', {'notes': notes})

@login_required
def upvote_note(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    Upvote.objects.get_or_create(user=request.user, note=note)
    return redirect('view_note', note_id=note.id)

@login_required
def order_printout(request):
    if request.method == 'POST':
        form = PrintOrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            # Count pages in the PDF using the updated method
            pdf = request.FILES['pdf_file']
            pdf_reader = PdfReader(pdf)
            order.page_count = len(pdf_reader.pages)

            # Calculate price
            order.calculate_price()

            # Save the order
            order.save()

            return redirect('order_success')
    else:
        form = PrintOrderForm()

    return render(request, 'order_printout.html', {'form': form})

def order_success(request):
    return render(request, 'order_success.html')

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'my_orders.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_detail.html', {'order': order})

@login_required
def profile_view(request):
    user = request.user
    # profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        user.full_name = full_name

        # Handle date of birth parsing to ensure correct format
        dob_str = request.POST.get('dob')
        if dob_str:
            try:
                user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            except ValueError:
                return render(request, 'profile.html', {
                    'error': 'Invalid date format. Please use YYYY-MM-DD.',
                    'full_name': user.full_name,
                    'dob': dob_str,
                    'semester': request.POST.get('semester'),
                    'year': request.POST.get('year'),
                    'branch': request.POST.get('branch'),
                    'email': request.POST.get('email'),
                })

        user.semester = request.POST.get('semester')
        user.year = request.POST.get('year')
        user.branch = request.POST.get('branch')
        user.email = request.POST.get('email')
        user.save()

        return redirect('profile')

    context = {
        'username': user.username,
        'full_name': user.full_name,
        'dob': user.dob.strftime('%Y-%m-%d') if user.dob else '',
        'semester': user.semester,
        'year': user.year,
        'branch': user.branch,
        'email': user.email,
    }

    return render(request, 'profile.html', context)

@login_required
def rewards_view(request):
    # Fetch the user's badges from the database
    # Assuming you have a UserProfile model or similar to store badges
    badges = request.user.badges.all() # Adjust according to your data model
    
    context = {
        'badges': badges,
    }
    
    return render(request, 'rewards.html', context)  # Create rewards.html template