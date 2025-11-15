from django.urls import path
from .views import AppointmentHealthCheckView, ClinicianSearchView, ClinicianAvailabilityView, AppointmentBookingView, ClinicianDashboardView, ClinicianScheduleManagementView, ClinicianScheduleDeleteView, AppointmentStatusUpdateView
from django.urls import path

urlpatterns = [
    path('health/', AppointmentHealthCheckView.as_view(), name='appointments-health'),
    path('search/', ClinicianSearchView.as_view(), name='clinician-search'),
    path('availability/<int:clinician_id>/', ClinicianAvailabilityView.as_view(), name='clinician-availability'),
    path('book/', AppointmentBookingView.as_view(), name='appointment-book'),
    path('dashboard/', ClinicianDashboardView.as_view(), name='clinician-dashboard'),
    path('schedule/', ClinicianScheduleManagementView.as_view(), name='admin-schedule-manage'),
    path('schedule/<int:pk>/', ClinicianScheduleDeleteView.as_view(), name='admin-schedule-delete'),
    path('status/<str:appointment_id>/', AppointmentStatusUpdateView.as_view(), name='appointment-status-update'),
    
]