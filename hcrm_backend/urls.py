from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('authentication.urls')),
    path('api/v1/patients/', include('patients.urls')),
    path('api/v1/appointments/', include('appointments.urls')),
    path('api/v1/records/', include('electronic_records.urls')),
]