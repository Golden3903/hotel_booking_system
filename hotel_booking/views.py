from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Room, Booking, UserProfile
from .forms import AddRoomForm, BookingApprovalForm, RoomForm, UserRegisterForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm

# Home and Admin Views
def index(request):
    rooms = Room.objects.all()
    return render(request, 'hotel_booking/index.html', {'rooms': rooms})

@staff_member_required
@login_required
def admin_home(request):
    rooms = Room.objects.all()
    bookings = Booking.objects.all()
    return render(request, 'hotel_booking/admin_home.html', {
        'rooms': rooms,
        'bookings': bookings
    })

# Room Management Views
def add_room(request):
    if request.method == 'POST':
        form = AddRoomForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room added successfully!')
            return redirect('admin_home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AddRoomForm()
    return render(request, 'hotel_booking/add_room.html', {'form': form})

def available_rooms(request):
    rooms = Room.objects.all()
    return render(request, 'hotel_booking/available_rooms.html', {'rooms': rooms})

def room_details(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, 'hotel_booking/room_details.html', {'room': room})

def edit_room(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, 'Room updated successfully!')
            return redirect('admin_home')
    else:
        form = RoomForm(instance=room)
    return render(request, 'hotel_booking/edit_room.html', {'form': form, 'room': room})

def delete_room(request, id):
    room = get_object_or_404(Room, id=id)
    room.delete()
    messages.success(request, 'Room deleted successfully!')
    return redirect('admin_home')

# Booking Views
@login_required
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    if request.method == 'POST':
        guest_name = request.POST['name']
        guest_email = request.POST['email']
        duration = int(request.POST['duration'])

        check_in_date = timezone.now().date()
        check_out_date = check_in_date + timezone.timedelta(days=duration)

        booking = Booking.objects.create(
            room=room,
            guest_name=guest_name,
            guest_email=guest_email,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            user=request.user
        )

        # Redirect to payment QR page instead of directly to success page
        return redirect('payment_qr', booking_id=booking.id)

    return render(request, 'hotel_booking/book_room.html', {'room': room})

# Add a new view for the payment QR page
def payment_qr(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'hotel_booking/payment_qr.html', {'booking': booking})

def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'hotel_booking/booking_success.html', {'booking': booking})

@staff_member_required
def approve_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        form = BookingApprovalForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Booking status updated!')
            return redirect('view_bookings')
    else:
        form = BookingApprovalForm(instance=booking)
    return render(request, 'hotel_booking/approve_booking.html', {
        'booking': booking,
        'form': form
    })

@staff_member_required
def view_bookings(request):
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'hotel_booking/view_bookings.html', {'bookings': bookings})

@staff_member_required
def manage_rooms(request):
    rooms = Room.objects.all()
    return render(request, 'hotel_booking/manage_rooms.html', {'rooms': rooms})

# User Authentication Views
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}!')
            return redirect('index')
    else:
        form = UserRegisterForm()
    return render(request, 'hotel_booking/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('index')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'hotel_booking/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('index')

# User Profile Views
@login_required
def edit_profile(request):
    # 获取或创建用户资料
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()

            # 处理头像上传
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
                profile.save()

            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('user_profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'hotel_booking/edit_profile.html', {'form': form, 'profile': profile})

@login_required
def user_profile(request):
    # Get user information and booking history
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'hotel_booking/user_profile.html', {'bookings': bookings, 'profile': profile})

# Contact View
def contact_us(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()

            # Validate required fields
            if not all([name, email, subject, message]):
                messages.error(request, "All fields are required.")
                return render(request, 'hotel_booking/contact_us.html', {
                    'form_data': {
                        'name': name,
                        'email': email,
                        'subject': subject,
                        'message': message
                    }
                })

            # Create and save contact message
            from .models import ContactMessage
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

            messages.success(request, "✔ Message sent successfully")
            return redirect('contact_us')

        except Exception as e:
            messages.error(request, "Sorry, there was an error sending your message. Please try again.")
            return render(request, 'hotel_booking/contact_us.html')

    return render(request, 'hotel_booking/contact_us.html')