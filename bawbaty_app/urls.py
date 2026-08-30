from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet, 
    ServiceViewSet, 
    AppointmentViewSet, 
    RequestViewSet,
    ComplaintViewSet,   # <-- استيراد واجهة الشكاوى
    DashboardStatsView  
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'complaints', ComplaintViewSet, basename='complaint') # <-- تسجيل مسار الشكاوى الجديد

urlpatterns = [
    # مسار واجهة الإحصائيات المخصصة
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    
    # مسارات الروتر الافتراضية
    path('', include(router.urls)),
]