from django.urls import path
from .views import AppointmentHealthCheckView


urlpatterns = [
    path('health/', AppointmentHealthCheckView.as_view(), name='appointments-health'),
]
