from rest_framework import viewsets, filters, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
import uuid

from .models import (
    UserAccount,
    Department,
    Service,
    Appointment,
    Request,
    AuditLog,
    Complaint
)
from .serializers import (
    DepartmentSerializer,
    ServiceSerializer,
    AppointmentSerializer,
    RequestSerializer,
    ComplaintSerializer
)

# --- واجهة إنشاء حساب جديد (تسجيل المواطنين) ---
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        national_id = data.get('national_id')
        phone_number = data.get('phone_number')
        full_name = data.get('full_name')
        password = data.get('password')

        # التحقق من وجود جميع البيانات المطلوبة
        if not all([national_id, phone_number, full_name, password]):
            return Response(
                {"error": "يرجى تزويد جميع البيانات المطلوبة: الرقم الوطني، رقم الهاتف، الاسم الكامل، وكلمة المرور."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # التحقق من عدم وجود الرقم الوطني سابقاً
        if UserAccount.objects.filter(national_id=national_id).exists():
            return Response(
                {"error": "الرقم الوطني مُسجَّل بالفعل في النظام."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # إنشاء حساب المستخدم باستعمال UserAccountManager
            user = UserAccount.objects.create_user(
                national_id=national_id,
                phone_number=phone_number,
                full_name=full_name,
                password=password,
            ) # type: ignore
            return Response(
                {
                    "message": "تم إنشاء الحساب بنجاح",
                    "user": {
                        "id": user.id,
                        "national_id": user.national_id,
                        "full_name": user.full_name,
                        "role": user.role
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"حدث خطأ أثناء إنشاء الحساب: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

# واجهة الدوائر (قراءة فقط)
class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]

# واجهة الخدمات (قراءة فقط - تدعم قائمة الخدمات وإرجاع تفاصيل الخدمة حسب ID تلقائياً عبر Router)
class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'is_active']
    search_fields = ['name', 'description']

# واجهة مخصصة إضافية للحصول على بيانات خدمة معينة من خلال الـ ID في الـ URL
class ServiceDetailView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

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

# واجهة الطلبات والمعاملات
class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen':
            return Request.objects.filter(citizen=user)
        elif user.role == 'employee':
            return Request.objects.filter(service__department=user.department)
        return Request.objects.all()

    def perform_create(self, serializer):
        serializer.save(
            citizen=self.request.user,
            tracking_id=uuid.uuid4()
        )

    def perform_update(self, serializer):
        old_instance = self.get_object()
        previous_status = old_instance.status
        updated_request = serializer.save()
        
        if previous_status != updated_request.status:
            AuditLog.objects.create(
                request=updated_request,
                action_by=self.request.user,
                previous_status=previous_status,
                new_status=updated_request.status
            )

# واجهة الشكاوى
class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen':
            return Complaint.objects.filter(user=user)
        return Complaint.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# واجهة الإحصائيات للوحة التحكم (Dashboard)
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        requests_today = Request.objects.filter(created_at__date=today).count()
        audit_count = AuditLog.objects.count()
        
        data = {
            "average_execution_time": "18 دقيقة",
            "compliance_rate": "94.2%",
            "requests_today": requests_today,
            "audit_logs_count": audit_count
        }
        
        return Response(data)