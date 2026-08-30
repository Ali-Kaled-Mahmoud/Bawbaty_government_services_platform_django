from rest_framework import serializers
from .models import Department, Service, Appointment, Request, Complaint # تمت إضافة Complaint

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class ServiceSerializer(serializers.ModelSerializer):
    # إضافة هذا السطر ليرسل لزملائك "اسم الدائرة" بدلاً من إرسال "رقمها" فقط
    department_name = serializers.CharField(source='department.name', read_only=True)
    
    class Meta:
        model = Service
        fields = '__all__'

class AppointmentSerializer(serializers.ModelSerializer):
    # هذه الأسطر لتوضيح الأسماء في الـ JSON بدلاً من إرسال أرقام الـ (ID) المعقدة
    citizen_name = serializers.CharField(source='citizen.full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        # حقل المواطن وحالة الموعد للقراءة فقط، لأننا سنتحكم بها برمجياً لاحقاً
        read_only_fields = ['citizen', 'status']

class RequestSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source='citizen.full_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Request
        fields = '__all__'
        read_only_fields = ['citizen', 'tracking_number', 'submitted_at', 'updated_at']

# --- الكلاس الجديد الخاص بالشكاوى ---
class ComplaintSerializer(serializers.ModelSerializer):
    # لإرسال اسم المواطن للواجهات الأمامية لتسهيل العرض
    citizen_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Complaint
        fields = '__all__'
        # الحقول التي لا يمكن للمواطن التعديل عليها يدوياً
        read_only_fields = ['user', 'ai_classification', 'status', 'created_at']