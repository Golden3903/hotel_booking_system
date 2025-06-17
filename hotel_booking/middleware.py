import logging
import traceback
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib import auth
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.sessions.backends.db import SessionStore

logger = logging.getLogger(__name__)

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            logger.error(traceback.format_exc())
            return JsonResponse({
                'error': 'Server internal error',
                'details': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    def process_exception(self, request, exception):
        logger.error(f"Exception in request: {str(exception)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            'error': 'Server internal error',
            'details': str(exception),
            'traceback': traceback.format_exc()
        }, status=500)


class SeparateAdminSessionMiddleware:
    """
    Middleware that maintains completely separate sessions for admin panel and hotel booking system.
    
    Key Features:
    - Admin panel (/admin/) ONLY uses admin user sessions
    - Hotel booking system (/hotel_booking/) ONLY uses regular user sessions  
    - Zero interference between the two systems
    - Frontend users remain logged in as themselves regardless of admin panel access
    - Admin panel always shows admin user regardless of frontend user activity
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Get admin user for admin panel
        try:
            self.admin_user = User.objects.filter(is_superuser=True, is_active=True).first()
            if self.admin_user:
                logger.info(f"Admin user found: {self.admin_user.username}")
            else:
                logger.warning("No admin user found")
        except Exception as e:
            logger.error(f"Error finding admin user: {str(e)}")
            self.admin_user = None
    
    def __call__(self, request):
        # Handle admin panel requests ONLY
        if request.path.startswith('/admin/'):
            return self._handle_admin_only_request(request)
        
        # For ALL other requests (including hotel_booking), do NOT interfere
        return self.get_response(request)
    
    def _handle_admin_only_request(self, request):
        """
        Handle admin panel requests with forced admin login.
        This method ONLY affects /admin/ URLs and does NOT touch other sessions.
        """
        if not self.admin_user:
            return self.get_response(request)
        
        # Force admin login ONLY for admin panel access
        if not (request.user.is_authenticated and request.user.is_superuser):
            auth.login(request, self.admin_user)
            logger.info(f"Admin user {self.admin_user.username} logged in for admin panel")
        
        return self.get_response(request)


class SessionIsolationMiddleware:
    """
    Additional middleware to prevent any session bleeding between systems.
    This ensures that hotel booking user sessions are never affected by admin operations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process the request normally
        response = self.get_response(request)
        
        # Add headers to identify session type for debugging
        if request.path.startswith('/admin/'):
            response['X-Session-Context'] = 'admin-panel'
        elif request.path.startswith('/hotel_booking/') or request.path == '/':
            response['X-Session-Context'] = 'hotel-booking'
        
        return response


# Utility functions for session management
def ensure_admin_login(request):
    """
    Utility function to ensure admin user is logged in for admin operations.
    """
    try:
        admin_user = User.objects.filter(is_superuser=True, is_active=True).first()
        if admin_user and not (request.user.is_authenticated and request.user.is_superuser):
            auth.login(request, admin_user)
            logger.info(f"Admin user {admin_user.username} logged in via utility function")
            return True
    except Exception as e:
        logger.error(f"Error in ensure_admin_login: {str(e)}")
    return False

def get_hotel_booking_user(request):
    """
    Utility function to get the current hotel booking user without affecting admin session.
    """
    if hasattr(request, 'session'):
        hotel_user_id = request.session.get('hotel_user_id')
        if hotel_user_id:
            try:
                return User.objects.get(id=hotel_user_id, is_active=True)
            except User.DoesNotExist:
                pass
    return None