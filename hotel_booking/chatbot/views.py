from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.db import connection
from django.db.utils import OperationalError
from django.contrib.auth.decorators import login_required
from ..models import Room, Booking
from django.contrib.auth.models import User
from .dialog_manager import DialogManager
import json
import re
from datetime import datetime, date, timedelta
import dateutil.parser
import logging
import uuid
from django.utils.crypto import get_random_string

# Configure logging
logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def chatbot_api(request):
    """Enhanced chatbot API with improved error handling and English responses"""
    session_data = {}  # Initialize session_data at the beginning

    try:
        # Test database connection
        connection.ensure_connection()
        logger.info("Database connection successful")
    except OperationalError as e:
        logger.error(f"Database connection error: {str(e)}")
        return JsonResponse({
            'error': 'Database connection error',
            'message': 'Sorry, we are experiencing technical difficulties. Please try again later.',
            'session': session_data
        }, status=500)

    try:
        # Log request with proper datetime import
        logger.info(f"Received chat request at {datetime.now()}")
        logger.debug(f"Request headers: {dict(request.headers)}")
        logger.debug(f"Request body: {request.body.decode('utf-8')}")

        if not request.body:
            logger.warning("Empty request body")
            return JsonResponse({
                'error': 'Bad request',
                'message': 'Please provide a message to continue our conversation.',
                'session': session_data
            }, status=400)

        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return JsonResponse({
                'error': 'Invalid JSON',
                'message': 'Sorry, there was an error processing your request. Please try again.',
                'session': session_data
            }, status=400)

        # Validate required fields
        if 'message' not in data:
            logger.warning("Missing 'message' field in request")
            return JsonResponse({
                'error': 'Bad request',
                'message': 'Please provide a message to continue our conversation.',
                'session': session_data
            }, status=400)

        # Get user message and session data
        user_message = data.get('message', '').strip()
        session_data = data.get('session', {})
        user_id = data.get('user_id')

        logger.info(f"User input: {user_message}")
        logger.info(f"Current session state: {session_data.get('state')}")
        logger.info(f"Current user data: {session_data.get('user_data')}")

        # Get current user (if authenticated)
        user = None
        if request.user.is_authenticated:
            user = request.user
            if 'user_data' not in session_data:
                session_data['user_data'] = {}
            session_data['user_data']['username'] = user.username
        elif user_id:
            try:
                user = User.objects.get(id=user_id)
                if 'user_data' not in session_data:
                    session_data['user_data'] = {}
                session_data['user_data']['username'] = user.username
                logger.info(f"Found user by ID: {user.username} (ID: {user.id})")
            except User.DoesNotExist:
                logger.warning(f"User with ID {user_id} not found")
                pass
            except Exception as e:
                logger.error(f"Error getting user by ID {user_id}: {str(e)}")
                pass

        # Initialize DialogManager
        dialog_manager = DialogManager()

        # Check if user is a returning customer before processing
        if 'user_data' not in session_data:
            session_data['user_data'] = {}

        # Check for returning customer by looking for previous successful bookings
        returning_customer_info = check_returning_customer_by_context(user_message, session_data)
        if returning_customer_info:
            session_data['user_data']['is_returning_customer'] = True
            # Pre-fill guest information from previous booking
            session_data['user_data'].update({
                'guest_name': returning_customer_info['guest_name'],
                'email': returning_customer_info['email'],
                'phone': returning_customer_info['phone']
            })
        else:
            session_data['user_data']['is_returning_customer'] = False

        # Add user information to session data for dialog manager
        if user:
            session_data['user_data']['user_id'] = user.id
            session_data['user_data']['user'] = user  # Keep for dialog manager use

        # Process message
        response, updated_session = dialog_manager.process(user_message, session_data)

        logger.info(f"Updated session state: {updated_session.get('state')}")
        logger.info(f"Updated user data: {updated_session.get('user_data')}")
        logger.info(f"Generated response: {response}")

        # 只在新预订 booking_confirmed 时处理 confirmation - 更严格的重复检查
        booking_id = updated_session.get('user_data', {}).get('booking_id')
        previous_booking_id = session_data.get('user_data', {}).get('booking_id')
        confirmation_already_sent = (
            updated_session.get('user_data', {}).get('confirmation_sent', False) or
            session_data.get('user_data', {}).get('confirmation_sent', False)
        )

        # 检查是否是新的预订确认（不是重复的消息）
        # 额外检查：确保这个booking_id没有被确认过
        confirmed_booking_id = session_data.get('user_data', {}).get('confirmation_booking_id')

        is_new_booking_confirmation = (
            updated_session.get('state') == 'booking_confirmed' and
            booking_id and
            not confirmation_already_sent and
            not (session_data.get('state') in ['extending_stay', 'upgrading_room', 'cancelling_booking']) and
            (not previous_booking_id or booking_id != previous_booking_id or
             session_data.get('state') != 'booking_confirmed') and  # 确保不是重复的确认状态
            booking_id != confirmed_booking_id  # 确保这个booking_id没有被确认过
        )

        logger.info(f"Booking confirmation check - State: {updated_session.get('state')}, "
                   f"Booking ID: {booking_id}, Previous ID: {previous_booking_id}, "
                   f"Confirmation sent: {confirmation_already_sent}, "
                   f"Will show confirmation: {is_new_booking_confirmation}")

        show_booking_confirmation = is_new_booking_confirmation
        if show_booking_confirmation:
            user_data = updated_session.get('user_data', {})
            booking_id = user_data.get('booking_id')

            logger.info(f"Sending booking confirmation for booking ID: {booking_id}")

            # 立即标记确认消息已发送，防止重复发送
            updated_session['user_data']['confirmation_sent'] = True
            updated_session['user_data']['confirmation_booking_id'] = booking_id  # 记录已确认的booking_id

            room_type = user_data.get('room_type')
            room = Room.objects.filter(name__icontains=room_type).first() or Room.objects.first()

            if room:
                try:
                    check_in = dateutil.parser.parse(user_data.get('check_in_date')).date()
                    check_out = dateutil.parser.parse(user_data.get('check_out_date')).date()

                    # Create booking record
                    booking = Booking.objects.create(
                        room=room,
                        guest_name=user_data.get('guest_name'),
                        guest_email=user_data.get('email'),
                        guest_phone=user_data.get('phone', ''),
                        check_in_date=check_in,
                        check_out_date=check_out,
                        status='approved',  # 使用正确的状态值
                        user=request.user if request.user.is_authenticated else None,
                        booking_id=booking_id  # 直接使用booking_id变量
                    )

                    logger.info(f"Created booking record: {booking.id} for booking_id: {booking_id}")

                    # 生成确认消息（只发送一次）
                    confirmation_message = f"""Your booking has been confirmed. Your booking ID is: {booking_id}. You can use this ID to check your booking status or make changes. Here are your booking details:
Room Type: {room_type}
Check-in Date: {check_in}
Check-out Date: {check_out}
Name: {user_data.get('guest_name')}
Email: {user_data.get('email')}
Phone: {user_data.get('phone', '')}
Is there anything else I can help you with?"""

                    response = confirmation_message

                    logger.info(f"Booking confirmation sent successfully for booking ID: {booking_id}")

                    # 重置状态，准备下次预订，但保留确认标记
                    updated_session['state'] = 'greeting'
                    updated_session['user_data'] = {
                        'is_returning_customer': True,  # 保留回头客标记
                        'confirmation_sent': True,  # 保留确认标记
                        'confirmation_booking_id': booking_id  # 保留已确认的booking_id
                    }
                    dialog_manager.state = 'greeting'
                    dialog_manager.user_data = {
                        'is_returning_customer': True,
                        'confirmation_sent': True,
                        'confirmation_booking_id': booking_id
                    }

                    # Send confirmation email
                    try:
                        send_booking_confirmation(user_data)
                    except Exception as e:
                        logger.error(f"Failed to send confirmation email: {str(e)}")
                except Exception as e:
                    logger.error(f"Error creating booking record: {str(e)}")
                    import traceback
                    logger.error(f"Full traceback: {traceback.format_exc()}")
                    # 如果预订创建失败，不要发送确认消息
                    show_booking_confirmation = False

        # Handle booking cancellation
        if updated_session.get('state') == 'cancelling_booking':
            user_data = updated_session.get('user_data', {})
            booking_id = user_data.get('cancel_booking_id')
            email = user_data.get('cancel_email')

            try:
                booking = None
                if booking_id:
                    booking = Booking.objects.filter(booking_id=booking_id).first()
                elif email:
                    booking = Booking.objects.filter(guest_email=email).first()

                if booking:
                    booking.status = 'cancelled'
                    booking.save()
                    response = f"Your booking {booking.booking_id or booking.id} has been successfully cancelled. You will receive a confirmation email shortly."
                    logger.info(f"Booking cancelled: {booking.id}")
                else:
                    response = "Sorry, we couldn't find your booking. Please check your booking ID or email address and try again."

                # 添加状态重置逻辑
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

            except Exception as e:
                logger.error(f"Error cancelling booking: {str(e)}")
                response = "Sorry, there was an error processing your cancellation. Please try again later or contact customer service."
                # 即使出错也要重置状态
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

        # Handle room upgrade
        if updated_session.get('state') == 'upgrading_room':
            user_data = updated_session.get('user_data', {})
            booking_id = user_data.get('upgrade_booking_id')
            email = user_data.get('upgrade_email')
            new_room_type = user_data.get('new_room_type')

            try:
                booking = None
                if booking_id:
                    booking = Booking.objects.filter(booking_id=booking_id).first()
                elif email:
                    booking = Booking.objects.filter(guest_email=email).first()

                if booking and new_room_type:
                    new_room = Room.objects.filter(name__icontains=new_room_type).first()
                    if new_room:
                        old_room = booking.room.name
                        booking.room = new_room
                        booking.save()
                        response = f"Your room has been successfully upgraded from {old_room} to {new_room.name}. You will receive a confirmation email shortly."
                        logger.info(f"Room upgraded for booking: {booking.id}")
                    else:
                        response = f"Sorry, we don't have {new_room_type} rooms available. Please choose from our available room types."
                else:
                    response = "Sorry, we couldn't find your booking. Please check your booking ID or email address and try again."
            except Exception as e:
                logger.error(f"Error upgrading room: {str(e)}")
                response = "Sorry, there was an error processing your room upgrade. Please try again later or contact customer service."
                # 即使出错也要重置状态
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

        # Handle date change
        if updated_session.get('state') == 'changing_date':
            user_data = updated_session.get('user_data', {})
            booking_id = user_data.get('change_booking_id')
            email = user_data.get('change_email')
            new_check_in = user_data.get('new_check_in_date')  # 字段名已经正确
            new_check_out = user_data.get('new_check_out_date')  # 添加check_out_date支持

            try:
                booking = None
                if booking_id:
                    booking = Booking.objects.filter(booking_id=booking_id).first()
                elif email:
                    booking = Booking.objects.filter(guest_email=email).first()

                if booking and new_check_in:
                    today = date.today()
                    days_until_checkin = (booking.check_in_date - today).days

                    if days_until_checkin >= 3:
                        try:
                            new_check_in_date = dateutil.parser.parse(new_check_in).date()
                            # 如果提供了新的check_out日期，使用它；否则保持原有的住宿天数
                            if new_check_out:
                                new_check_out_date = dateutil.parser.parse(new_check_out).date()
                            else:
                                duration = (booking.check_out_date - booking.check_in_date).days
                                new_check_out_date = new_check_in_date + timedelta(days=duration)

                            # Check room availability for new dates
                            available, message = check_room_availability(booking.room.name, new_check_in_date, new_check_out_date)

                            if available:
                                booking.check_in_date = new_check_in_date
                                booking.check_out_date = new_check_out_date
                                booking.save()
                                response = f"Your check-in date has been successfully changed to {new_check_in_date}. Your new check-out date is {new_check_out_date}."
                                logger.info(f"Check-in date changed for booking: {booking.id}")
                            else:
                                response = f"Sorry, your room is not available for the new dates. {message}"
                        except Exception as e:
                            logger.error(f"Error parsing new date: {str(e)}")
                            response = "Sorry, please provide a valid date in the format YYYY-MM-DD."
                    else:
                        response = "Sorry, check-in date changes are only allowed at least 3 days before your original check-in date."
                else:
                    response = "Sorry, we couldn't find your booking. Please check your booking ID or email address and try again."

                # 添加状态重置逻辑
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

            except Exception as e:
                logger.error(f"Error changing date: {str(e)}")
                response = "Sorry, there was an error processing your date change. Please try again later or contact customer service."
                # 即使出错也要重置状态
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

        # Handle stay extension
        if updated_session.get('state') == 'extending_stay':
            user_data = updated_session.get('user_data', {})
            booking_id = user_data.get('extend_booking_id')
            email = user_data.get('extend_email')
            additional_nights = user_data.get('additional_nights')
            # 修复：同时检查两个字段名
            new_checkout_date = user_data.get('new_checkout_date') or user_data.get('extend_until_date')

            try:
                booking = None
                if booking_id:
                    booking = Booking.objects.filter(booking_id=booking_id).first()
                elif email:
                    booking = Booking.objects.filter(guest_email=email).first()

                if booking:
                    today = date.today()

                    # Check if guest is currently checked in or will check in soon
                    if booking.check_in_date <= today <= booking.check_out_date or booking.check_in_date > today:
                        try:
                            if not additional_nights and not new_checkout_date:
                                response = "Please specify either the number of additional nights or your new checkout date."
                            else:
                                if additional_nights:
                                    nights = int(additional_nights)
                                    new_checkout = booking.check_out_date + timedelta(days=nights)
                                elif new_checkout_date:
                                    new_checkout = dateutil.parser.parse(new_checkout_date).date()
                                    nights = (new_checkout - booking.check_out_date).days

                                # Check room availability for extended period
                                available, message = check_room_availability(booking.room.name, booking.check_out_date, new_checkout)

                                if available:
                                    additional_cost = booking.room.price * nights
                                    booking.check_out_date = new_checkout
                                    booking.save()
                                    response = f"Your stay has been successfully extended to {new_checkout}. Additional cost: RM{additional_cost}. You will receive a confirmation email shortly."
                                    logger.info(f"Stay extended for booking: {booking.id}")
                                else:
                                    response = f"Sorry, your room is not available for the extended period. {message}"
                        except (ValueError, TypeError) as e:
                            logger.error(f"Error parsing extension details: {str(e)}")
                            response = "Sorry, please provide a valid number of nights or checkout date."
                            # 即使出错也要重置状态
                            updated_session['state'] = 'greeting'
                            updated_session['user_data'] = {}
                            dialog_manager.state = 'greeting'
                            dialog_manager.user_data = {}
                    else:
                        response = "Sorry, stay extensions are only available for current guests or upcoming bookings."
                        # 重置状态
                        updated_session['state'] = 'greeting'
                        updated_session['user_data'] = {}
                        dialog_manager.state = 'greeting'
                        dialog_manager.user_data = {}
                else:
                    response = "Sorry, we couldn't find your booking. Please check your booking ID or email address and try again."
                    # 重置状态
                    updated_session['state'] = 'greeting'
                    updated_session['user_data'] = {}
                    dialog_manager.state = 'greeting'
                    dialog_manager.user_data = {}
            except Exception as e:
                logger.error(f"Error extending stay: {str(e)}")
                response = "Sorry, there was an error processing your stay extension. Please try again later or contact customer service."
                # 即使出错也要重置状态
                updated_session['state'] = 'greeting'
                updated_session['user_data'] = {}
                dialog_manager.state = 'greeting'
                dialog_manager.user_data = {}

        # Clean session data for JSON serialization (remove User objects)
        import copy
        clean_session = copy.deepcopy(updated_session)
        if 'user_data' in clean_session and 'user' in clean_session['user_data']:
            del clean_session['user_data']['user']
            logger.info("Removed User object from session for JSON serialization")

        # Prepare response data
        response_data = {
            'message': response,
            'session': clean_session
        }

        # Add delayed messages if present
        if hasattr(dialog_manager, 'delayed_messages') and dialog_manager.delayed_messages:
            response_data['delayed_messages'] = dialog_manager.delayed_messages

        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Unhandled exception in chatbot_api: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # Clean session data for error response too
        import copy
        clean_error_session = copy.deepcopy(session_data)
        if 'user_data' in clean_error_session and 'user' in clean_error_session['user_data']:
            del clean_error_session['user_data']['user']

        return JsonResponse({
            'message': 'Sorry, I am temporarily unable to process your request. Please provide more details such as check-in date, check-out date, and room type.',
            'session': clean_error_session
        }, status=500)

@login_required
def chatbot_view(request):
    """Render the chatbot interface - requires user authentication"""
    rooms = Room.objects.all()
    return render(request, 'hotel_booking/chatbot.html', {'rooms': rooms})

def send_booking_confirmation(session):
    """Send booking confirmation email"""
    try:
        subject = f"Hotel Booking Confirmation - Booking #{session['booking_id']}"
        message = f"""Dear {session['guest_name']},

Thank you for booking with us. Your booking details are as follows:

Booking Reference: {session['booking_id']}
Room: {session['room_type']}
Check-in Date: {session['check_in_date']}
Check-out Date: {session['check_out_date']}
Duration: {session.get('duration', 'Not specified')} nights
Total Cost: ${session.get('total_cost', 'Not specified')}

We look forward to welcoming you to our hotel.

Best regards,
Hotel Management
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [session['email']],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def check_room_availability(room_type, check_in_date, check_out_date):
    """Check if rooms of the specified type are available for the given dates"""
    try:
        rooms = Room.objects.filter(name__icontains=room_type)
        if not rooms.exists():
            return False, "No rooms of this type found"

        overlapping_bookings = Booking.objects.filter(
            room__in=rooms,
            status__in=['pending', 'approved']
        ).filter(
            Q(check_in_date__lt=check_out_date) & Q(check_out_date__gt=check_in_date)
        )

        available_count = rooms.count() - overlapping_bookings.count()
        if available_count > 0:
            return True, f"{available_count} {room_type} room(s) available"
        else:
            return False, f"No {room_type} rooms available for these dates"
    except Exception as e:
        return False, f"Error checking availability: {str(e)}"

def create_booking(session, user=None):
    """Create a booking from session data"""
    try:
        room_type = session.get('room_type')
        room = Room.objects.filter(name__icontains=room_type).first() or Room.objects.first()
        if not room:
            raise Exception("No rooms available")

        try:
            check_in = datetime.strptime(session['check_in_date'], '%Y-%m-%d').date()
        except ValueError:
            check_in = dateutil.parser.parse(session['check_in_date']).date()

        try:
            check_out = datetime.strptime(session['check_out_date'], '%Y-%m-%d').date()
        except ValueError:
            check_out = dateutil.parser.parse(session['check_out_date']).date()

        duration = (check_out - check_in).days
        total_cost = room.price * duration

        booking = Booking.objects.create(
            room=room,
            guest_name=session['guest_name'],
            guest_email=session['email'],
            guest_phone=session.get('phone', ''),
            check_in_date=check_in,
            check_out_date=check_out,
            user=user,
            status='pending',
            booking_id=session.get('booking_id')
        )

        session['duration'] = duration
        session['total_cost'] = total_cost
        return booking.booking_id
    except Exception as e:
        logger.error(f"Error creating booking: {str(e)}")
        return f"BK-ERR-{uuid.uuid4().hex[:8].upper()}"


def check_returning_customer_by_context(user_message, session_data):
    """
    Check if user is a returning customer by analyzing the message context
    and looking for previous bookings in the database.
    """
    import re

    # Extract email from user message if present
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    email_match = email_pattern.search(user_message)

    # Extract name patterns (common names that might indicate returning customer)
    name_patterns = [
        r'\b(?:I am|I\'m|My name is|This is)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b',
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:here|speaking|again)\b'
    ]

    potential_name = None
    for pattern in name_patterns:
        name_match = re.search(pattern, user_message, re.IGNORECASE)
        if name_match:
            potential_name = name_match.group(1).strip()
            break

    # Check database for previous bookings
    if email_match:
        email = email_match.group()
        previous_booking = Booking.objects.filter(
            guest_email=email,
            status__in=['approved', 'completed']
        ).first()
        if previous_booking:
            return {
                'guest_name': previous_booking.guest_name,
                'email': previous_booking.guest_email,
                'phone': previous_booking.guest_phone or ''
            }

    if potential_name:
        previous_booking = Booking.objects.filter(
            guest_name__icontains=potential_name,
            status__in=['approved', 'completed']
        ).first()
        if previous_booking:
            return {
                'guest_name': previous_booking.guest_name,
                'email': previous_booking.guest_email,
                'phone': previous_booking.guest_phone or ''
            }

    # Check session data for any stored user info that might indicate returning customer
    stored_email = session_data.get('user_data', {}).get('email')
    if stored_email:
        previous_booking = Booking.objects.filter(
            guest_email=stored_email,
            status__in=['approved', 'completed']
        ).first()
        if previous_booking:
            return {
                'guest_name': previous_booking.guest_name,
                'email': previous_booking.guest_email,
                'phone': previous_booking.guest_phone or ''
            }

    return None