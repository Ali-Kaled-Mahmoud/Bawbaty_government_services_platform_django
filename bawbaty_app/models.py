from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid

# --- هذا هو الكلاس الجديد الذي يعلم النظام كيف ينشئ الحسابات بالرقم الوطني ---
class UserAccountManager(BaseUserManager):
    def create_user(self, national_id, phone_number, full_name, password=None, **extra_fields):
        if not national_id:
            raise ValueError("يجب إدخال الرقم الوطني")
        user = self.model(
            national_id=national_id,
            phone_number=phone_number,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, national_id, phone_number, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(national_id, phone_number, full_name, password, **extra_fields)


 # --- جدول المستخدمين بعد ربطه بالمدير الجديد ---
class UserAccount(AbstractUser):
    ROLE_CHOICES = [
        ('citizen', 'مواطن'),
        ('employee', 'موظف'),
        ('admin', 'مدير/مسؤول'),
    ]
    username = None  # قمنا بإلغاء اسم المستخدم الافتراضي
    national_id = models.CharField(max_length=20, unique=True, verbose_name="الرقم الوطني")
    phone_number = models.CharField(max_length=15, verbose_name="رقم الهاتف")
    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen', verbose_name="الصلاحية")
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="جهة العمل (للموظفين)")

    USERNAME_FIELD = 'national_id'
    REQUIRED_FIELDS = ['phone_number', 'full_name']

    objects = UserAccountManager() # type: ignore # <-- هذا هو السطر السحري الذي يربط الجدول بالحل

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})" # type: ignore

# 2. جدول الدوائر الحكومية
class Department(models.Model):
    name = models.CharField(max_length=255, verbose_name="اسم الدائرة")
    branch_name = models.CharField(max_length=255, verbose_name="اسم الفرع")

    def __str__(self):
        return f"{self.name} - {self.branch_name}"

# جدول الخدمات
class Service(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='services', verbose_name="الدائرة الحكومية")
    name = models.CharField(max_length=200, verbose_name="اسم الخدمة")
    
    # --- الحقول الجديدة لتطابق الواجهات ---
    description = models.TextField(blank=True, null=True, verbose_name="وصف الخدمة")
    fees = models.CharField(max_length=100, default='مجانية', verbose_name="الرسوم")
    execution_time = models.CharField(max_length=100, default='فوري', verbose_name="مدة التنفيذ")
    # ----------------------------------------
    
    is_active = models.BooleanField(default=True, verbose_name="متاحة")

    def __str__(self):
        return self.name
        
# 4. جدول المواعيد
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('confirmed', 'مؤكد'),
        ('completed', 'مكتمل'),
        ('canceled', 'ملغي'),
    ]
    citizen = models.ForeignKey(UserAccount, on_delete=models.CASCADE, verbose_name="المواطن")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="الدائرة الحكومية")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="الخدمة المطلوبة")
    appointment_date = models.DateField(verbose_name="تاريخ الموعد")
    appointment_time = models.TimeField(verbose_name="وقت الموعد")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الموعد")

    def __str__(self):
        return f"موعد {self.citizen.full_name} - {self.service.name}"

# 5. جدول الطلبات والمعاملات
class Request(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'تقديم الطلب'),
        ('auditing', 'التدقيق الإداري'),
        ('matching', 'المطابقة والاستلام'),
        ('closed', 'إغلاق المعاملة'),
        ('rejected', 'مرفوض'), # حالة إضافية للرفض تظهر للموظف
    ]
    tracking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="رقم التتبع")
    citizen = models.ForeignKey(UserAccount, on_delete=models.CASCADE, verbose_name="المواطن")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="الخدمة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted', verbose_name="حالة الطلب")
    payment_status = models.BooleanField(default=False, verbose_name="حالة الدفع")
    receipt_reference = models.CharField(max_length=255, null=True, blank=True, verbose_name="رقم الإيصال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التقديم")

    def __str__(self):
        return str(self.tracking_id)

# 6. جدول سجل التدقيق (Audit Log) لضمان الشفافية
class AuditLog(models.Model):
    request = models.ForeignKey(Request, on_delete=models.CASCADE, verbose_name="المعاملة")
    action_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, verbose_name="بواسطة الموظف/المسؤول")
    previous_status = models.CharField(max_length=50, verbose_name="الحالة السابقة")
    new_status = models.CharField(max_length=50, verbose_name="الحالة الجديدة")
    action_time = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإجراء")

    def __str__(self):
        return f"تعديل على {self.request.tracking_id}"
    
#7. جدول تذاكر الدعم والشكاوى (الأساس لنموذج الذكاء الاصطناعي)
class SupportTicket(models.Model):
    TICKET_TYPES = [
        ('INQUIRY', 'استفسار عام عن خدمة'),
        ('COMPLAINT', 'شكوى'),
        ('SUGGESTION', 'اقتراح'),
        ('TECH_ISSUE', 'مشكلة تقنية')
    ]

    # --- بيانات المواطن المُرسِل ---
    full_name = models.CharField(max_length=200, verbose_name="الاسم الكامل")
    national_id = models.CharField(max_length=15, verbose_name="الرقم الوطني / الهوية")
    phone_number = models.CharField(max_length=20, verbose_name="رقم الهاتف المحمول")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    
    # --- تفاصيل الرسالة ---
    ticket_type = models.CharField(max_length=50, choices=TICKET_TYPES, verbose_name="نوع الطلب / الاستفسار")
    subject = models.CharField(max_length=255, blank=True, null=True, verbose_name="عنوان الموضوع")
    details = models.TextField(verbose_name="تفاصيل الرسالة")
    
    # --- حقول الإدارة والذكاء الاصطناعي (تُعبأ لاحقاً) ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    ai_classification = models.CharField(max_length=100, blank=True, null=True, verbose_name="تصنيف الذكاء الاصطناعي") # حقل مخصص لنتيجة نموذجك!
    is_resolved = models.BooleanField(default=False, verbose_name="تم الحل")

    def __str__(self):
        return f"{self.get_ticket_type_display()} - {self.full_name}" # type: ignore

    # جدول الشكاوى
class Complaint(models.Model):
    # ربط الشكوى بالمواطن الذي قدمها
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='complaints')
    
    # تفاصيل الشكوى
    subject = models.CharField(max_length=255, verbose_name="عنوان الشكوى")
    description = models.TextField(verbose_name="تفاصيل الشكوى")
    
    # حقل مخصص ليقوم الذكاء الاصطناعي بتصنيف الشكوى لاحقاً
    ai_classification = models.CharField(max_length=100, blank=True, null=True, verbose_name="تصنيف الذكاء الاصطناعي")
    
    # حالة الشكوى لمتابعتها
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'تم الحل'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    
    # تاريخ تقديم الشكوى (يُضاف تلقائياً)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"شكوى: {self.subject} - {self.user.national_id}" # type: ignore