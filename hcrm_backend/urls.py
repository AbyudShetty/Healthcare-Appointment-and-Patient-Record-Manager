from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/patients/', include('patients.urls')),
    path('api/v1/appointments/', include('appointments.urls')),
    path('api/v1/records/', include('electronic_records.urls')),
    path('api/v1/reports/', include('reporting.urls')),
    path('api/v1/admin/reminders/', include('notifications.urls')),
    path('api/v1/admin/users/', include('authentication.admin_urls')),
    path('api/v1/admin/logs/', include('audit_logs.urls')), 
]
