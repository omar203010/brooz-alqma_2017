from django.contrib import admin
from django.utils.html import format_html
from .models import Unit, Booking, Report, Contract, UserProfile, Visit
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    """إدارة الوحدات في لوحة التحكم"""
    
    list_display = ['name', 'owner', 'status_badge', 'created_at']
    list_filter = ['is_available', 'created_at', 'owner']
    search_fields = ['name', 'owner__username', 'owner__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('name', 'owner')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """عرض حالة الوحدة بشكل مرئي"""
        if obj.is_available:
            color = '#28a745'
            text = 'متاح'
        else:
            color = '#dc3545'
            text = 'مؤجر'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, text
        )
    status_badge.short_description = 'الحالة'
    
    def image_preview(self, obj):
        """معاينة الصورة في لوحة التحكم"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; '
                'border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "لا توجد صورة"
    image_preview.short_description = 'معاينة الصورة'


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    """إدارة الحجوزات في لوحة التحكم"""
    
    list_display = ['unit', 'start_date', 'end_date', 'price_per_day', 'cash_amount', 'transfer_amount', 'customer_name', 'customer_phone', 'duration', 'created_at']
    list_filter = ['unit', 'start_date', 'end_date', 'created_at']
    search_fields = ['unit__name', 'customer_name', 'customer_phone']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('معلومات الحجز', {
            'fields': ('unit', 'start_date', 'end_date', 'price_per_day')
        }),
        ('المدفوعات', {
            'fields': ('cash_amount', 'transfer_amount')
        }),
        ('معلومات العميل', {
            'fields': ('customer_name', 'customer_phone', 'notes')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def duration(self, obj):
        """حساب مدة الحجز"""
        delta = obj.end_date - obj.start_date
        return f"{delta.days + 1} يوم"
    duration.short_description = 'المدة'
    
    def save_model(self, request, obj, form, change):
        """حفظ الحجز مع معالجة الأخطاء"""
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'خطأ في الحفظ: {str(e)}')


# تخصيص لوحة التحكم
admin.site.site_header = "بروز القمة العقارية - لوحة التحكم"
admin.site.site_title = "إدارة الوحدات"
admin.site.index_title = "مرحباً بك في لوحة التحكم"


# إضافة رابط تقارير المدفوعات داخل admin
from django.urls import path
from django.utils.html import format_html
from django.urls import reverse

def payment_reports_admin_view(request):
    """توجيه من admin إلى صفحة التقارير"""
    from django.shortcuts import redirect
    return redirect('units:payment_reports')

# إضافة URL مخصص في admin
admin_site = admin.site
if not getattr(admin_site, '_brooz_urls_patched', False):
    _orig_get_urls = admin_site.get_urls

    def get_urls_with_reports():
        """إضافة URLs للتقارير داخل admin (patch مرة واحدة فقط)"""
        from django.urls import path
        urls = _orig_get_urls()
        custom_urls = [
            path('payment-reports/', admin_site.admin_view(payment_reports_admin_view), name='payment_reports_redirect'),
        ]
        return custom_urls + urls

    admin_site.get_urls = get_urls_with_reports
    admin_site._brooz_urls_patched = True


 

@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    """إدارة الزيارات في لوحة التحكم"""
    
    list_display = ['user_display', 'visit_count_display', 'path_display', 'ip_address', 'visit_date', 'user_agent_short']
    list_filter = ['created_at', 'path']
    search_fields = ['user__username', 'user__email', 'ip_address', 'path']
    readonly_fields = ['user', 'session_key', 'ip_address', 'user_agent', 'path', 'referer', 'created_at']
    date_hierarchy = 'created_at'
    change_list_template = 'admin/units/visit_change_list.html'
    
    def get_queryset(self, request):
        """عرض فقط زيارات المستثمرين (استبعاد admin/staff)"""
        qs = super().get_queryset(request)
        # استبعاد زيارات admin/staff من القائمة
        qs = qs.exclude(user__is_staff=True).exclude(user__is_superuser=True)
        return qs.select_related('user')
    
    def changelist_view(self, request, extra_context=None):
        """إضافة إحصائيات حسب المستخدم المحدد"""
        extra_context = extra_context or {}
        
        # الحصول على المستخدم المحدد من الفلتر
        user_id = request.GET.get('user__id__exact')
        
        if user_id:
            try:
                from django.contrib.auth.models import User
                selected_user = User.objects.get(id=user_id)
                # حساب الزيارات فقط إذا كان المستخدم ليس admin/staff
                if not selected_user.is_staff and not selected_user.is_superuser:
                    visit_count = Visit.objects.filter(user=selected_user).count()
                    extra_context['selected_user'] = selected_user
                    extra_context['user_visit_count'] = visit_count
            except:
                pass
        
        # إحصائيات عامة لجميع المستخدمين (فقط المستثمرين، بدون admin/staff)
        from django.db.models import Count
        user_stats = (
            Visit.objects
            .filter(user__isnull=False)
            .exclude(user__is_staff=True)
            .exclude(user__is_superuser=True)
            .values('user__username', 'user__email', 'user__id')
            .annotate(total_visits=Count('id'))
            .order_by('-total_visits')
        )
        extra_context['user_stats'] = list(user_stats)
        
        # حساب عدد الزيارات لكل مستخدم لتخزينه في cache (فقط المستثمرين)
        from django.db.models import Count as CountFunc
        visit_counts_dict = dict(
            Visit.objects
            .filter(user__isnull=False)
            .exclude(user__is_staff=True)
            .exclude(user__is_superuser=True)
            .values('user_id')
            .annotate(count=CountFunc('id'))
            .values_list('user_id', 'count')
        )
        self._visit_counts_cache = visit_counts_dict
        
        return super().changelist_view(request, extra_context)
    
    def user_display(self, obj):
        """عرض المستخدم"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.user.username,
                obj.user.email if obj.user.email else 'بدون بريد'
            )
        return format_html('<span style="color: #999;">زائر غير مسجل</span>')
    user_display.short_description = 'المستخدم'
    user_display.admin_order_field = 'user__username'
    
    def visit_count_display(self, obj):
        """عرض عدد الزيارات للمستخدم (يظهر فقط في القائمة) - فقط للمستثمرين"""
        if obj.user:
            # تجاهل admin/staff
            if obj.user.is_staff or obj.user.is_superuser:
                return format_html('<span style="color: #999;">-</span>')
            
            # استخدام cache إذا كان متاحاً
            if hasattr(self, '_visit_counts_cache'):
                count = self._visit_counts_cache.get(obj.user_id, 0)
            else:
                # حساب مباشر (يستخدم في حالة عدم وجود cache)
                count = Visit.objects.filter(user=obj.user).count()
            
            return format_html(
                '<span style="background: linear-gradient(135deg, #a89078 0%, #8b7765 100%); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 14px;">{}</span>',
                count
            )
        return '-'
    visit_count_display.short_description = 'عدد الزيارات'
    
    def path_display(self, obj):
        """عرض المسار بشكل مختصر"""
        path = obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
        return format_html('<code style="font-size: 11px;">{}</code>', path)
    path_display.short_description = 'المسار'
    
    def visit_date(self, obj):
        """عرض تاريخ الزيارة بشكل منسق"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    visit_date.short_description = 'تاريخ الزيارة'
    visit_date.admin_order_field = 'created_at'
    
    def user_agent_short(self, obj):
        """عرض معلومات المتصفح بشكل مختصر"""
        if obj.user_agent:
            ua = obj.user_agent[:60] + '...' if len(obj.user_agent) > 60 else obj.user_agent
            return format_html('<small>{}</small>', ua)
        return '-'
    user_agent_short.short_description = 'المتصفح'
    
    def has_add_permission(self, request):
        """منع إضافة زيارات يدوياً"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """منع تعديل الزيارات"""
        return False





 
    
    def user_display(self, obj):
        """عرض المستخدم"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.user.username,
                obj.user.email if obj.user.email else 'بدون بريد'
            )
        return format_html('<span style="color: #999;">زائر غير مسجل</span>')
    user_display.short_description = 'المستخدم'
    user_display.admin_order_field = 'user__username'
    
    def visit_count_display(self, obj):
        """عرض عدد الزيارات للمستخدم (يظهر فقط في القائمة) - فقط للمستثمرين"""
        if obj.user:
            # تجاهل admin/staff
            if obj.user.is_staff or obj.user.is_superuser:
                return format_html('<span style="color: #999;">-</span>')
            
            # استخدام cache إذا كان متاحاً
            if hasattr(self, '_visit_counts_cache'):
                count = self._visit_counts_cache.get(obj.user_id, 0)
            else:
                # حساب مباشر (يستخدم في حالة عدم وجود cache)
                count = Visit.objects.filter(user=obj.user).count()
            
            return format_html(
                '<span style="background: linear-gradient(135deg, #a89078 0%, #8b7765 100%); color: white; padding: 4px 12px; border-radius: 15px; font-weight: bold; font-size: 14px;">{}</span>',
                count
            )
        return '-'
    visit_count_display.short_description = 'عدد الزيارات'
    
    def path_display(self, obj):
        """عرض المسار بشكل مختصر"""
        path = obj.path[:50] + '...' if len(obj.path) > 50 else obj.path
        return format_html('<code style="font-size: 11px;">{}</code>', path)
    path_display.short_description = 'المسار'
    
    def visit_date(self, obj):
        """عرض تاريخ الزيارة بشكل منسق"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    visit_date.short_description = 'تاريخ الزيارة'
    visit_date.admin_order_field = 'created_at'
    
    def user_agent_short(self, obj):
        """عرض معلومات المتصفح بشكل مختصر"""
        if obj.user_agent:
            ua = obj.user_agent[:60] + '...' if len(obj.user_agent) > 60 else obj.user_agent
            return format_html('<small>{}</small>', ua)
        return '-'
    user_agent_short.short_description = 'المتصفح'
    
    def has_add_permission(self, request):
        """منع إضافة زيارات يدوياً"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """منع تعديل الزيارات"""
        return False



from django.urls import path
from django.utils.html import format_html
from django.urls import reverse

def payment_reports_admin_view(request):
    """توجيه من admin إلى صفحة التقارير"""
    from django.shortcuts import redirect
    return redirect('units:payment_reports')

# إضافة URL مخصص في admin
admin_site = admin.site
if not getattr(admin_site, '_brooz_urls_patched', False):
    _orig_get_urls = admin_site.get_urls

    def get_urls_with_reports():
        """إضافة URLs للتقارير داخل admin (patch مرة واحدة فقط)"""
        from django.urls import path
        urls = _orig_get_urls()
        custom_urls = [
            path('payment-reports/', admin_site.admin_view(payment_reports_admin_view), name='payment_reports_redirect'),
        ]
        return custom_urls + urls

    admin_site.get_urls = get_urls_with_reports
    admin_site._brooz_urls_patched = True


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['title', 'owner__username', 'owner__email']
    fields = ['owner', 'title', 'file']


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created_at']
    list_filter = ['owner', 'created_at']
    search_fields = ['title', 'owner__username', 'owner__email']
    fields = ['owner', 'title', 'file']


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'معلومات إضافية'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# إلغاء تسجيل User الافتراضي وإعادة تسجيله مع CustomUserAdmin
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number']
    search_fields = ['user__username', 'user__email', 'phone_number']
