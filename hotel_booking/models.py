from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

class BookingAddon(models.Model):
    ADDON_TYPES = [
        ('breakfast', 'Breakfast Service'),
        ('transport', 'Airport Transfer Service'),
    ]

    TRANSPORT_DIRECTIONS = [
        ('to_hotel', 'To Hotel'),
        ('from_hotel', 'From Hotel'),
    ]

    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='addons')
    addon_type = models.CharField(max_length=20, choices=ADDON_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Breakfast specific fields
    breakfast_count = models.IntegerField(null=True, blank=True, help_text="Number of people for breakfast")

    # Transport specific fields
    transport_direction = models.CharField(max_length=20, choices=TRANSPORT_DIRECTIONS, null=True, blank=True)
    transport_date = models.DateField(null=True, blank=True)
    transport_time = models.TimeField(null=True, blank=True)
    passenger_count = models.IntegerField(null=True, blank=True, help_text="Number of passengers (max 5)")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.addon_type == 'breakfast':
            return f"Breakfast for {self.breakfast_count} people - RM{self.price}"
        elif self.addon_type == 'transport':
            return f"Transport ({self.get_transport_direction_display()}) - RM{self.price}"
        return f"{self.get_addon_type_display()} - RM{self.price}"

    def get_total_price(self):
        if self.addon_type == 'breakfast' and self.breakfast_count:
            return self.price * self.breakfast_count
        return self.price

    class Meta:
        verbose_name = "Booking Add-on"
        verbose_name_plural = "Booking Add-ons"

class RoomServiceRequest(models.Model):
    SERVICE_TYPES = [
        ('cleaning', 'Room Cleaning'),
        ('dnd', 'Do Not Disturb'),
    ]

    CLEANING_TIME_SLOTS = [
        ('now', 'Now'),
        ('after_2pm', 'After 2 PM'),
        ('tomorrow_morning', 'Tomorrow Morning'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='room_services')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Cleaning specific fields
    cleaning_time_slot = models.CharField(max_length=20, choices=CLEANING_TIME_SLOTS, null=True, blank=True)
    special_instructions = models.TextField(blank=True, help_text="Special cleaning instructions")

    # DND specific fields
    dnd_active = models.BooleanField(default=False, help_text="Is Do Not Disturb currently active")
    dnd_start_time = models.DateTimeField(null=True, blank=True)
    dnd_end_time = models.DateTimeField(null=True, blank=True)

    # Common fields
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Staff notes")

    def __str__(self):
        if self.service_type == 'cleaning':
            return f"Cleaning request for {self.booking.booking_id} - {self.get_cleaning_time_slot_display()}"
        elif self.service_type == 'dnd':
            status = "Active" if self.dnd_active else "Inactive"
            return f"DND for {self.booking.booking_id} - {status}"
        return f"{self.get_service_type_display()} for {self.booking.booking_id}"

    class Meta:
        verbose_name = "Room Service Request"
        verbose_name_plural = "Room Service Requests"
        ordering = ['-requested_at']

class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField(default=2)
    image = models.ImageField(upload_to='room_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.info(f"Room saved: {self.name} (ID: {self.id})")
        except Exception as e:
            logger.error(f"Error saving Room {self.name}: {str(e)}")
            raise

    @classmethod
    def get_available_rooms(cls, check_in_date, check_out_date):
        try:
            # Find rooms that are booked during the requested period
            booked_rooms = Booking.objects.filter(
                check_in_date__lt=check_out_date,
                check_out_date__gt=check_in_date,
                status__in=['pending', 'approved']  # Consider both pending and approved bookings
            ).values_list('room_id', flat=True)
            available_rooms = cls.objects.exclude(id__in=booked_rooms)
            logger.info(f"Available rooms found: {available_rooms.count()} for dates {check_in_date} to {check_out_date}")
            return available_rooms
        except Exception as e:
            logger.error(f"Error getting available rooms: {str(e)}")
            return cls.objects.none()

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=100)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_id = models.CharField(max_length=20, unique=True, blank=True, null=True)  # Added for unique booking identifier
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.guest_name} - {self.room.name} ({self.booking_id or 'No ID'})"

    def save(self, *args, **kwargs):
        # Validate dates
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                logger.error(f"Invalid booking dates for {self.guest_name}: check-out {self.check_out_date} is not after check-in {self.check_in_date}")
                raise ValueError("Check-out date must be after check-in date")
            if self.check_in_date < timezone.now().date():
                logger.error(f"Invalid booking dates for {self.guest_name}: check-in {self.check_in_date} is in the past")
                raise ValueError("Check-in date cannot be in the past")

        try:
            super().save(*args, **kwargs)
            logger.info(f"Booking saved: {self.booking_id or self.id} for {self.guest_name}")
        except Exception as e:
            logger.error(f"Error saving Booking for {self.guest_name}: {str(e)}")
            raise

    def clean(self):
        # Additional validation for Django admin or forms
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError("Check-out date must be after check-in date")
            if self.check_in_date < timezone.now().date():
                raise ValidationError("Check-in date cannot be in the past")

    def get_duration(self):
        return (self.check_out_date - self.check_in_date).days

    def get_total_price(self):
        return self.room.price * self.get_duration()

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Your Name")
    email = models.EmailField(verbose_name="Email Address")
    subject = models.CharField(max_length=200, verbose_name="Subject")
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False, verbose_name="Read Status")
    replied = models.BooleanField(default=False, verbose_name="Replied")

    def __str__(self):
        return f"{self.name} - {self.subject}"

    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ['-created_at']