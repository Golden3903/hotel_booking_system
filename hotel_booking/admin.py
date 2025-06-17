from django.contrib import admin
from .models import Room, Booking, UserProfile, BookingAddon, RoomServiceRequest, ContactMessage

# Register your models here.

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'capacity', 'created_at']
    list_filter = ['capacity', 'created_at']
    search_fields = ['name', 'description']

class BookingAddonInline(admin.TabularInline):
    model = BookingAddon
    extra = 0
    readonly_fields = ['created_at']

class RoomServiceInline(admin.TabularInline):
    model = RoomServiceRequest
    extra = 0
    readonly_fields = ['requested_at']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'guest_name', 'room', 'check_in_date', 'check_out_date', 'status', 'get_total_with_addons', 'created_at']
    list_filter = ['status', 'created_at', 'check_in_date']
    search_fields = ['booking_id', 'guest_name', 'guest_email']
    readonly_fields = ['created_at']
    inlines = [BookingAddonInline, RoomServiceInline]

    def get_total_with_addons(self, obj):
        base_price = obj.get_total_price()
        addon_total = sum(addon.get_total_price() for addon in obj.addons.all())
        return f"RM{base_price + addon_total:.2f}"
    get_total_with_addons.short_description = 'Total (with add-ons)'

@admin.register(BookingAddon)
class BookingAddonAdmin(admin.ModelAdmin):
    list_display = ['booking', 'addon_type', 'get_details', 'get_total_price', 'created_at']
    list_filter = ['addon_type', 'created_at']
    search_fields = ['booking__booking_id', 'booking__guest_name']
    readonly_fields = ['created_at']

    def get_details(self, obj):
        if obj.addon_type == 'breakfast':
            return f"{obj.breakfast_count} guests"
        elif obj.addon_type == 'transport':
            direction = obj.get_transport_direction_display()
            return f"{direction} - {obj.transport_date} {obj.transport_time} ({obj.passenger_count} passengers)"
        return "-"
    get_details.short_description = 'Details'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user__email']
    search_fields = ['user__username', 'user__email']

@admin.register(RoomServiceRequest)
class RoomServiceRequestAdmin(admin.ModelAdmin):
    list_display = ['booking', 'service_type', 'status', 'get_service_details', 'requested_at']
    list_filter = ['service_type', 'status', 'requested_at']
    search_fields = ['booking__booking_id', 'booking__guest_name']
    readonly_fields = ['requested_at']

    def get_service_details(self, obj):
        if obj.service_type == 'cleaning':
            return f"Time: {obj.get_cleaning_time_slot_display()}" if obj.cleaning_time_slot else "Time: Not specified"
        elif obj.service_type == 'dnd':
            status = "Active" if obj.dnd_active else "Inactive"
            return f"Status: {status}"
        return "-"
    get_service_details.short_description = 'Service Details'

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'replied', 'created_at']
    list_filter = ['is_read', 'replied', 'created_at']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at']

    # Make the message field read-only in the list view
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['name', 'email', 'subject', 'message']
        return self.readonly_fields

    # Custom actions
    actions = ['mark_as_read', 'mark_as_replied']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = 'Mark selected messages as read'

    def mark_as_replied(self, request, queryset):
        updated = queryset.update(replied=True)
        self.message_user(request, f'{updated} messages marked as replied.')
    mark_as_replied.short_description = 'Mark selected messages as replied'
