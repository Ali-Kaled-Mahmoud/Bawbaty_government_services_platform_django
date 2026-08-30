from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Department, Service, Appointment, Request, AuditLog, Complaint 
from .serializers import DepartmentSerializer, ServiceSerializer, AppointmentSerializer, RequestSerializer, ComplaintSerializer
import uuid # استيراد مكتبة توليد أرقام التتبع الفريدة
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone

# واجهة الدوائر (قراءة فقط)
class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

# واجهة الخدمات (قراءة فقط)
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    
    # --- الإضافات الجديدة للبحث والفلترة ---
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    
    # تحديد الحقول القابلة للفلترة (مثلاً الفلترة برقم الدائرة أو حالة الخدمة)
    filterset_fields = ['department', 'is_active']
    
    # تحديد الحقول القابلة للبحث النصي
    search_fields = ['name', 'description']
    # ---------------------------------------

# واجهة المواعيد
class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen':
            return Appointment.objects.filter(citizen=user)
        elif user.role == 'employee':
            return Appointment.objects.filter(department=user.department)
        return Appointment.objects.all()

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)

# واجهة الطلبات والمعاملات (الجديدة)
class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # 1. المواطن يرى طلباته الخاصة فقط
        if user.role == 'citizen':
            return Request.objects.filter(citizen=user)
        # 2. الموظف يرى الطلبات المرتبطة بالخدمات التي تقدمها دائرته
        elif user.role == 'employee':
            return Request.objects.filter(service__department=user.department)
        # 3. المدير يرى جميع الطلبات في النظام
        return Request.objects.all()

    def perform_create(self, serializer):
        # توليد رقم تتبع فريد يبدأ بـ REQ متبوعاً بـ 8 أحرف وأرقام عشوائية
        unique_tracking_number = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        
        # حفظ الطلب مع ربطه بالمواطن ورقم التتبع آلياً
        serializer.save(
            citizen=self.request.user,
            tracking_number=unique_tracking_number
        )

    def perform_update(self, serializer):
        # 1. جلب الطلب من قاعدة البيانات لمعرفة حالته القديمة قبل التعديل
        old_instance = self.get_object()
        previous_status = old_instance.status
        
        # 2. حفظ التعديلات الجديدة التي أدخلها الموظف
        updated_request = serializer.save()
        
        # 3. المقارنة: إذا قام الموظف بتغيير الحالة فعلياً، ننشئ سجلاً فورياً في صندوق التدقيق
        if previous_status != updated_request.status:
            AuditLog.objects.create(
                request=updated_request,
                action_by=self.request.user,
                previous_status=previous_status,
                new_status=updated_request.status
            )

# --- واجهة الشكاوى الجديدة ---
class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # المواطن يرى شكاواه فقط
        if user.role == 'citizen':
            return Complaint.objects.filter(user=user)
        # المدير أو الموظف يرى جميع الشكاوى
        return Complaint.objects.all()

    def perform_create(self, serializer):
        # حفظ الشكوى وربطها بالمواطن صاحب التوكين آلياً
        serializer.save(user=self.request.user)
# -----------------------------

# واجهة الإحصائيات للوحة التحكم (Dashboard)
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # تحديد تاريخ اليوم
        today = timezone.now().date()
        
        # 1. حساب عدد الطلبات التي تم إنشاؤها اليوم
        requests_today = Request.objects.filter(created_at__date=today).count()
        
        # 2. حساب إجمالي عدد حركات وسجلات التدقيق
        audit_count = AuditLog.objects.count()
        
        # تجميع البيانات لإرسالها للواجهة الأمامية
        data = {
            "average_execution_time": "18 دقيقة",
            "compliance_rate": "94.2%",
            "requests_today": requests_today,
            "audit_logs_count": audit_count
        }
        
        return Response(data)