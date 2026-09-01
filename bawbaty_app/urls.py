from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet,
    RegisterView, 
    ServiceViewSet, 
    ServiceDetailView, # <-- استيراد واجهة تفاصيل الخدمة حسب الـ ID
    AppointmentViewSet, 
    RequestViewSet,
    ComplaintViewSet,
    DashboardStatsView  
)
# استيراد مكتبات التوكين
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'complaints', ComplaintViewSet, basename='complaint')

urlpatterns = [
    # مسار واجهة الإحصائيات المخصصة
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/register/', RegisterView.as_view(), name='register'),
    
    # مسار مخصص لجلب بيانات خدمة محددة باستخدام معرف الخدمة (ID)
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
        # الروابط الجديدة الخاصة بتسجيل الدخول وتوليد التوكين
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # مسارات الروتر الافتراضية
    path('', include(router.urls)),
]