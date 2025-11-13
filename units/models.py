from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import os

class UserProfile(models.Model):
    """ملف المستخدم لإضافة رقم الجوال"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الجوال'
    )

    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'

    def __str__(self):
        return f'{self.user.username} - {self.phone_number or "بدون رقم"}'


class Unit(models.Model):
    """نموذج الوحدة العقارية"""
    
    name = models.CharField(max_length=200, verbose_name="اسم الوحدة")
    description = models.TextField(verbose_name="الوصف", blank=True, null=True)
    image = models.ImageField(
        upload_to='units/',
        verbose_name="صورة الوحدة",
        blank=True,
        null=True
    )
    # تم حذف الحقول: capacity, has_pool, has_parking
    is_available = models.BooleanField(default=True, verbose_name="متاحة للحجز")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإضافة")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_units',
        verbose_name="مالك الوحدة"
    )
    
    class Meta:
        verbose_name = "وحدة"
        verbose_name_plural = "الوحدات"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_status_display_ar(self):
        """عرض حالة الوحدة بالعربية"""
        return "متاح" if self.is_available else "مؤجر"


class Booking(models.Model):
    """نموذج الحجز"""
    
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="الوحدة"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='unit_bookings',
        verbose_name='المستخدم',
        null=True,
        blank=True
    )
    start_date = models.DateField(verbose_name="تاريخ البداية")
    end_date = models.DateField(verbose_name="تاريخ النهاية")
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="اسم العميل"
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الهاتف"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )
    price_per_day = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="السعر لليوم"
    )
    cash_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ كاش"
    )
    transfer_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ تحويل"
    )
    is_owner_booking = models.BooleanField(
        default=False,
        verbose_name="حجز من المالك"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الحجز")
    
    class Meta:
        verbose_name = "حجز"
        verbose_name_plural = "الحجوزات"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.unit.name} - من {self.start_date} إلى {self.end_date}"
    
    def clean(self):
        """التحقق من صحة البيانات"""
        from django.core.exceptions import ValidationError
        
        if self.start_date and self.end_date:
            # السماح بحجز يوم واحد فقط
            if self.end_date != self.start_date:
                raise ValidationError({
                    'end_date': 'الحجز مسموح ليوم واحد فقط. يجب أن يساوي تاريخ النهاية تاريخ البداية.'
                })
            
            # التحقق من عدم تعارض الحجوزات
            overlapping_bookings = Booking.objects.filter(
                unit=self.unit,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date
            )
            
            # استثناء الحجز الحالي عند التعديل
            if self.pk:
                overlapping_bookings = overlapping_bookings.exclude(pk=self.pk)
            
            if overlapping_bookings.exists():
                raise ValidationError({
                    'start_date': 'يوجد حجز متعارض في هذه الفترة'
                })
    
    def save(self, *args, **kwargs):
        """حفظ الحجز مع التحقق"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def total_amount(self):
        """إجمالي المبلغ (كاش + تحويل)"""
        return (self.cash_amount or 0) + (self.transfer_amount or 0)


def validate_pdf(file_obj):
    name = getattr(file_obj, 'name', '')
    ext = os.path.splitext(name)[1].lower()
    if ext != '.pdf':
        raise ValidationError('يجب رفع ملف PDF فقط')


class Report(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='المالك'
    )
    title = models.CharField(max_length=255, verbose_name='العنوان')
    file = models.FileField(upload_to='reports/', validators=[validate_pdf], verbose_name='الملف (PDF)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'

    def __str__(self):
        return self.title


class Contract(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contracts',
        verbose_name='المالك'
    )
    title = models.CharField(max_length=255, verbose_name='العنوان')
    file = models.FileField(upload_to='contracts/', validators=[validate_pdf], verbose_name='الملف (PDF)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإضافة')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'عقد'
        verbose_name_plural = 'العقود'

    def __str__(self):
        return self.title


class Visit(models.Model):
    """نموذج لتتبع زيارات المستخدمين للموقع"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='visits',
        verbose_name='المستخدم',
        null=True,
        blank=True
    )
    session_key = models.CharField(
        max_length=40,
        verbose_name='مفتاح الجلسة',
        null=True,
        blank=True,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='عنوان IP',
        null=True,
        blank=True
    )
    user_agent = models.TextField(
        verbose_name='متصفح المستخدم',
        blank=True,
        null=True
    )
    path = models.CharField(
        max_length=500,
        verbose_name='مسار الصفحة',
        blank=True
    )
    referer = models.URLField(
        verbose_name='الصفحة المرجعية',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الزيارة',
        db_index=True
    )

    class Meta:
        verbose_name = 'زيارة'
        verbose_name_plural = 'الزيارات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        if self.user:
            return f'{self.user.username} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'
        return f'زائر غير مسجل - {self.created_at.strftime("%Y-%m-%d %H:%M")}'


class Expense(models.Model):
    """نموذج المصروفات للوحدات"""
    
    EXPENSE_CATEGORIES = [
        ('purchases_maintenance', 'مشتريات وصيانة'),
        ('cleaning_supplies', 'مواد نظافة'),
        ('chlorine', 'كلور'),
        ('electricity', 'كهرباء'),
        ('plumbing', 'سباكة'),
        ('swimming_pools', 'مسابح'),
        ('cooling', 'تبريد'),
        ('landscaping', 'زراعة وتشجير'),
        ('mattress_upholstery', 'تنجيد مراتب'),
        ('blacksmithing', 'حدادة'),
        ('carpentry', 'نجارة'),
        ('aluminum', 'ألمنيوم'),
        ('shared', 'مشتركة'),
        ('other', 'أخرى'),
    ]
    
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name="الوحدة"
    )
    category = models.CharField(
        max_length=50,
        choices=EXPENSE_CATEGORIES,
        verbose_name="فئة المصروف",
        blank=True,
        null=True
    )
    invoice = models.FileField(
        upload_to='expenses/invoices/',
        verbose_name="الفاتورة",
        blank=True,
        null=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="السعر",
        default=0
    )
    description = models.TextField(
        verbose_name="الوصف",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإضافة"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name="المالك"
    )
    
    class Meta:
        verbose_name = "مصروف"
        verbose_name_plural = "المصروفات"
        ordering = ['-created_at']
    
    def __str__(self):
        category_display = self.get_category_display() if self.category else 'بدون فئة'
        return f"{self.unit.name} - {category_display} - {self.price} ر.س"
    
    def get_category_display_ar(self):
        """الحصول على اسم الفئة بالعربية"""
        if self.category:
            return dict(self.EXPENSE_CATEGORIES).get(self.category, self.category)
        return 'بدون فئة'


class UnitPricing(models.Model):
    """نموذج أسعار تأجير الوحدات حسب أيام الأسبوع"""
    
    WEEKDAYS = [
        (0, 'الإثنين'),
        (1, 'الثلاثاء'),
        (2, 'الأربعاء'),
        (3, 'الخميس'),
        (4, 'الجمعة'),
        (5, 'السبت'),
        (6, 'الأحد'),
    ]
    
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='pricing',
        verbose_name="الوحدة"
    )
    day_of_week = models.IntegerField(
        choices=WEEKDAYS,
        verbose_name="يوم الأسبوع"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="سعر التأجير",
        default=0
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإضافة"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        verbose_name = "سعر الوحدة"
        verbose_name_plural = "أسعار الوحدات"
        unique_together = ['unit', 'day_of_week']
        ordering = ['unit', 'day_of_week']
    
    def __str__(self):
        return f"{self.unit.name} - {self.get_day_of_week_display()} - {self.price} ر.س"
    
    def get_day_of_week_display_ar(self):
        """الحصول على اسم اليوم بالعربية"""
        return dict(self.WEEKDAYS).get(self.day_of_week, '')


class UnitImage(models.Model):
    """صور إضافية للوحدة تظهر للمستخدم"""
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name='الوحدة'
    )
    image = models.ImageField(
        upload_to='units/gallery/',
        verbose_name='الصورة'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='عنوان الصورة',
        blank=True,
        null=True
    )
    description = models.TextField(
        verbose_name='وصف الصورة',
        blank=True,
        null=True
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='صورة مميزة'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة'
    )
    
    class Meta:
        verbose_name = 'صورة وحدة'
        verbose_name_plural = 'صور الوحدات'
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.title or f'صورة - {self.unit.name}'
