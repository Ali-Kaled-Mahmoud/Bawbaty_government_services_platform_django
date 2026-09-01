from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Department, Service, Appointment, Request, Complaint, UserAccount, AuditLog

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'national_id': self.user.national_id,
            'full_name': self.user.full_name,
            'role': self.user.role,
            'role_display': self.user.get_role_display(),
            'department_id': self.user.department.id if self.user.department else None,
        }
        return data

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source='citizen.full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['citizen', 'status']

# --- المحول المحدث للطلبات ---
class RequestSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source='citizen.full_name', read_only=True)
    citizen_national_id = serializers.CharField(source='citizen.national_id', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_fees = serializers.CharField(source='service.fees', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Request
        fields = '__all__'
        read_only_fields = ['citizen', 'tracking_id', 'created_at']

# --- محول سجل التدقيق ---
class AuditLogSerializer(serializers.ModelSerializer):
    action_by_name = serializers.CharField(source='action_by.full_name', read_only=True)

    class Meta:
        model = AuditLog
        fields = '__all__'

class ComplaintSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ['user', 'ai_classification', 'status', 'created_at']