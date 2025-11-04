from django.contrib import admin
from django.utils.html import format_html
from .models import Unit, Booking, Report, Contract, UserProfile
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
original_get_urls = admin_site.get_urls

def get_urls_with_reports():
    """إضافة URLs للتقارير داخل admin"""
    from django.urls import path
    urls = original_get_urls()
    custom_urls = [
        path('payment-reports/', admin_site.admin_view(payment_reports_admin_view), name='payment_reports_redirect'),
    ]
    return custom_urls + urls

admin_site.get_urls = get_urls_with_reports


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
