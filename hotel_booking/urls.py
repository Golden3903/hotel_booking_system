# hotel_booking/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .chatbot import views as chatbot_views

urlpatterns = [
    path('', views.index, name='index'),
    path('rooms/', views.available_rooms, name='available_rooms'),
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('payment_qr/<int:booking_id>/', views.payment_qr, name='payment_qr'),  # Add this new URL pattern
    path('booking_success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('add-room/', views.add_room, name='add_room'),
    path('room/<int:room_id>/', views.room_details, name='room_details'),
    path('admin_home/', views.admin_home, name='admin_home'),
    path('manage_rooms/', views.manage_rooms, name='manage_rooms'),
    path('edit_room/<int:id>/', views.edit_room, name='edit_room'),
    path('delete_room/<int:id>/', views.delete_room, name='delete_room'),
    path('add/', views.add_room, name='add_room'),
    path('edit/<int:room_id>/', views.edit_room, name='edit_room'),
    path('bookings/', views.view_bookings, name='view_bookings'),
    path('bookings/approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    # 添加聊天机器人URL
    path('chatbot/', chatbot_views.chatbot_view, name='chatbot'),
    path('chatbot/api/', chatbot_views.chatbot_api, name='chatbot_api'),
    # 在现有的urlpatterns列表中添加以下内容
    path('contact/', views.contact_us, name='contact_us'),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('user/logout/', views.user_logout, name='user_logout'),
    # 添加注册和登录URL
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    # 在urlpatterns列表中添加
    path('edit_profile/', views.edit_profile, name='edit_profile'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

