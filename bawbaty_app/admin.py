from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# تمت إضافة Complaint للاستيرادات في السطر التالي
from .models import UserAccount, Department, Service, Appointment, Request, AuditLog, Complaint

class CustomUserAdmin(UserAdmin):
    model = UserAccount
    # تم إضافة department لعرض جهة العمل في القائمة الرئيسية
    list_display = ('national_id', 'full_name', 'phone_number', 'role', 'department', 'is_active')
    # تم إضافة department للفلترة الجانبية
    list_filter = ('role', 'department', 'is_active')
    search_fields = ('national_id', 'full_name', 'phone_number')
    ordering = ('national_id',)
    
    # واجهة "تعديل" مستخدم موجود
    fieldsets = (
        ('المعلومات الأساسية', {'fields': ('national_id', 'password')}),
        ('التفاصيل الشخصية', {'fields': ('full_name', 'phone_number')}),
        # تم إضافة department هنا وتعديل العنوان
        ('الصلاحيات وجهة العمل', {'fields': ('role', 'department', 'is_active', 'is_staff', 'is_superuser')}),
    )

    # واجهة "إضافة" مستخدم جديد
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # تم إضافة department هنا ليتمكن المدير من تحديد الدائرة عند إضافة موظف
            'fields': ('national_id', 'phone_number', 'full_name', 'password', 'role', 'department'),
        }),
    )

admin.site.register(UserAccount, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Service)
admin.site.register(Appointment)
admin.site.register(Request)
admin.site.register(AuditLog)

# --- تسجيل واجهة الشكاوى الجديدة ---
@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'description')

admin.site.site_header = "لوحة إدارة بوابتي"
admin.site.site_title = "بوابتي"
admin.site.index_title = "إدارة منصة بوابتي"