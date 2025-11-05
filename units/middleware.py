"""
Middleware لتتبع زيارات المستخدمين للموقع
"""
from django.utils.deprecation import MiddlewareMixin
from .models import Visit
from django.utils import timezone


class VisitTrackingMiddleware(MiddlewareMixin):
    """
    Middleware لتسجيل كل زيارة للموقع
    """
    
    def process_request(self, request):
        """تسجيل الزيارة عند كل طلب"""
        # تجاهل طلبات AJAX والـ static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # تجاهل طلبات admin (نريد فقط تتبع زيارات الموقع الرئيسي)
        if request.path.startswith('/admin/'):
            return None
        
        # تجاهل طلبات API
        if request.path.startswith('/api/'):
            return None
        
        # الحصول على معلومات المستخدم
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # تجاهل زيارات الـ admin/staff - نحسب فقط زيارات المستثمرين (المستخدمين العاديين)
        if user and (user.is_staff or user.is_superuser):
            return None
        
        session_key = request.session.session_key
        
        # الحصول على معلومات الطلب
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        path = request.path
        referer = request.META.get('HTTP_REFERER', '')
        
        # تسجيل الزيارة (فقط للمستثمرين)
        try:
            Visit.objects.create(
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                path=path,
                referer=referer if referer else None
            )
        except Exception:
            # تجاهل الأخطاء في التسجيل لتجنب تعطيل الموقع
            pass
        
        return None
    
    def get_client_ip(self, request):
        """الحصول على عنوان IP الحقيقي للعميل"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

