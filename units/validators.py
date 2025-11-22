from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password as django_validate_password
import re


def validate_arabic_username(value):
    """التحقق من أن اسم المستخدم يحتوي على أحرف عربية أو إنجليزية أو أرقام"""
    if not value:
        raise ValidationError('اسم المستخدم مطلوب')
    
    # السماح بالأحرف العربية والإنجليزية والأرقام والمسافات والشرطة السفلية والنقطة
    # نطاقات Unicode للأحرف العربية:
    # \u0600-\u06FF: الأحرف العربية الأساسية
    # \u0750-\u077F: الأحرف العربية الإضافية
    # \u08A0-\u08FF: الأحرف العربية الممتدة
    # \uFB50-\uFDFF: أشكال الأحرف العربية
    # \uFE70-\uFEFF: أشكال الأحرف العربية الإضافية
    pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9_\s\.]+$'
    if not re.match(pattern, value):
        raise ValidationError('اسم المستخدم يجب أن يحتوي على أحرف عربية أو إنجليزية أو أرقام فقط')
    
    # التأكد من أن الاسم ليس فارغاً بعد إزالة المسافات
    if not value.strip():
        raise ValidationError('اسم المستخدم لا يمكن أن يكون فارغاً')


class NumericPasswordValidator:
    """التحقق من أن كلمة المرور تحتوي على أرقام فقط"""
    
    def validate(self, password, user=None):
        if not password:
            raise ValidationError('كلمة المرور مطلوبة')
        
        if not password.isdigit():
            raise ValidationError('كلمة المرور يجب أن تحتوي على أرقام فقط')
    
    def get_help_text(self):
        return 'كلمة المرور يجب أن تحتوي على أرقام فقط'

