from django.contrib.auth.models import User
from django.contrib import auth
import logging

logger = logging.getLogger(__name__)

def ensure_admin_logged_in(request):
    """
    Utility function to ensure admin user is logged in for admin panel access.
    Can be called from views that need to guarantee admin access.
    """
    try:
        admin_user = User.objects.filter(is_superuser=True, is_active=True).first()
        if admin_user and not (request.user.is_authenticated and request.user.is_superuser):
            auth.login(request, admin_user)
            logger.info(f"Ensured admin login for user: {admin_user.username}")
            return True
        return request.user.is_superuser if request.user.is_authenticated else False
    except Exception as e:
        logger.error(f"Error ensuring admin login: {str(e)}")
        return False

def get_hotel_booking_user(request):
    """
    Get the actual hotel booking user (not admin) from session.
    """
    if hasattr(request, 'session'):
        hotel_user_id = request.session.get('hotel_user_id')
        if hotel_user_id:
            try:
                return User.objects.get(id=hotel_user_id)
            except User.DoesNotExist:
                pass
    return None