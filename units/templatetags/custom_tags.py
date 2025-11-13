from django import template
from datetime import datetime

register = template.Library()

@register.filter
def arabic_date(date_obj):
    """تحويل التاريخ إلى صيغة عربية مع التقويم الميلادي"""
    if not date_obj:
        return ""
    
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except:
            try:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d %H:%M:%S').date()
            except:
                return date_obj
    
    months_arabic = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
        5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
        9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    
    day = date_obj.day
    month = months_arabic[date_obj.month]
    year = date_obj.year
    
    return f"{day} {month} {year}"


@register.filter
def mul(value, arg):
    """ضرب القيمة برقم"""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0




