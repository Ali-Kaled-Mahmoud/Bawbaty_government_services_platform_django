from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DepartmentViewSet,
    RegisterView, 
    ServiceViewSet, 
    ServiceDetailView,
    AppointmentViewSet, 
    RequestViewSet,
    AuditLogViewSet,
    ComplaintViewSet,
    DashboardStatsView,
    CustomTokenObtainPairView
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'complaints', ComplaintViewSet, basename='complaint')

urlpatterns = [
    path('dashboard-stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('services/<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    
    # مسار تسجيل الدخول المخصص
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('', include(router.urls)),
]