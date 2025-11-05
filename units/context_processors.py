"""
Context processors لإضافة إحصائيات الزيارات إلى templates
"""
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Visit


def visit_stats(request):
    """إضافة إحصائيات الزيارات إلى context"""
    if not request.path.startswith('/admin/'):
        return {}
    
    try:
        # إحصائيات شاملة (فقط للمستثمرين، بدون admin/staff)
        # استبعاد زيارات admin/staff من الإحصائيات
        total_visits = Visit.objects.exclude(user__is_staff=True).exclude(user__is_superuser=True).count()
        registered_visits = Visit.objects.filter(user__isnull=False).exclude(user__is_staff=True).exclude(user__is_superuser=True).count()
        anonymous_visits = Visit.objects.filter(user__isnull=True).count()
        
        # إحصائيات حسب المستخدم (فقط المستثمرين)
        user_visit_stats = (
            Visit.objects
            .filter(user__isnull=False)
            .exclude(user__is_staff=True)
            .exclude(user__is_superuser=True)
            .values('user__username', 'user__email')
            .annotate(visit_count=Count('id'))
            .order_by('-visit_count')[:20]
        )
        
        # إحصائيات اليوم (فقط المستثمرين)
        today = timezone.now().date()
        today_visits = Visit.objects.filter(created_at__date=today).exclude(user__is_staff=True).exclude(user__is_superuser=True).count()
        
        return {
            'total_visits': total_visits,
            'registered_visits': registered_visits,
            'anonymous_visits': anonymous_visits,
            'user_visit_stats': list(user_visit_stats),
            'today_visits': today_visits,
        }
    except Exception:
        # في حالة عدم وجود جدول الزيارات بعد (أثناء migrations)
        return {
            'total_visits': 0,
            'registered_visits': 0,
            'anonymous_visits': 0,
            'user_visit_stats': [],
            'today_visits': 0,
            'week_visits': 0,
            'month_visits': 0,
        }

