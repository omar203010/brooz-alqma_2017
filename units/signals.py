from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.validators import ASCIIUsernameValidator, UnicodeUsernameValidator
from .validators import validate_arabic_username


@receiver(class_prepared)
def remove_default_username_validator(sender, **kwargs):
    """إزالة الـ validator الافتراضي من حقل username في User model"""
    if sender == User:
        # إزالة الـ validators الافتراضية من حقل username
        username_field = sender._meta.get_field('username')
        # إزالة جميع الـ validators الافتراضية
        username_field.validators = [
            v for v in username_field.validators 
            if not isinstance(v, (ASCIIUsernameValidator, UnicodeUsernameValidator))
        ]
        # إضافة الـ validator المخصص
        username_field.validators.append(validate_arabic_username)

