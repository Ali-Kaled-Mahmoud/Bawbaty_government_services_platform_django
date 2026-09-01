from rest_framework import viewsets, filters, status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
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
    AuditLogSerializer,
    ComplaintSerializer,
    CustomTokenObtainPairSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        national_id = data.get('national_id')
        phone_number = data.get('phone_number')
        full_name = data.get('full_name')
        password = data.get('password')

        if not all([national_id, phone_number, full_name, password]):
            return Response(
                {"error": "يرجى تزويد جميع البيانات المطلوبة."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if UserAccount.objects.filter(national_id=national_id).exists():
            return Response(
                {"error": "الرقم الوطني مُسجَّل بالفعل في النظام."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = UserAccount.objects.create_user(
                national_id=national_id,
                phone_number=phone_number,
                full_name=full_name,
                password=password,
            ) # type: ignore
            return Response(
                {"message": "تم إنشاء الحساب بنجاح", "user": {"id": user.id, "national_id": user.national_id, "full_name": user.full_name, "role": user.role}},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({"error": f"حدث خطأ أثناء إنشاء الحساب: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [AllowAny]

class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'is_active']
    search_fields = ['name', 'description']

class ServiceDetailView(generics.RetrieveAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen':
            return Appointment.objects.filter(citizen=user)
        elif user.role == 'employee' and user.department:
            return Appointment.objects.filter(department=user.department)
        return Appointment.objects.all()

    def perform_create(self, serializer):
        serializer.save(citizen=self.request.user)

class RequestViewSet(viewsets.ModelViewSet):
    serializer_class = RequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'citizen':
            return Request.objects.filter(citizen=user)
        elif user.role == 'employee' and user.department:
            return Request.objects.filter(service__department=user.department)
        return Request.objects.all().order_by('-created_at')

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

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-action_time')
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

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

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        
        # 1. عدد المعاملات اليوم
        requests_today = Request.objects.filter(created_at__date=today).count()
        
        # 2. عدد سجلات التدقيق التراكمية
        audit_count = AuditLog.objects.count()

        # 3. حساب نسبة الالتزام بالمواعيد
        total_appointments = Appointment.objects.count()
        if total_appointments > 0:
            completed_appointments = Appointment.objects.filter(
                Q(status='completed') | Q(status='confirmed')
            ).count()
            compliance_rate_val = round((completed_appointments / total_appointments) * 100, 1)
        else:
            compliance_rate_val = 100.0

        # 4. حساب متوسط زمن الإنجاز للمعاملات المغلقة بناءً على سجلات التدقيق
        closed_logs = AuditLog.objects.filter(new_status='closed')
        if closed_logs.exists():
            total_seconds = 0
            count = 0
            for log in closed_logs:
                diff = log.action_time - log.request.created_at
                total_seconds += diff.total_seconds()
                count += 1
            avg_minutes = round((total_seconds / count) / 60)
            avg_exec_time = f"{avg_minutes} دقيقة" if avg_minutes > 0 else "أقل من دقيقة"
        else:
            avg_exec_time = "18 دقيقة"

        data = {
            "average_execution_time": avg_exec_time,
            "compliance_rate": f"{compliance_rate_val}%",
            "requests_today": requests_today,
            "audit_logs_count": audit_count
        }
        
        return Response(data)