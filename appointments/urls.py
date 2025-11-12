from django.urls import path
from .views import AppointmentHealthCheckView, ClinicianSearchView, ClinicianAvailabilityView, AppointmentBookingView, ClinicianDashboardView
from django.urls import path

urlpatterns = [
    path('health/', AppointmentHealthCheckView.as_view(), name='appointments-health'),
    path('search/', ClinicianSearchView.as_view(), name='clinician-search'),
    path('availability/<int:clinician_id>/', ClinicianAvailabilityView.as_view(), name='clinician-availability'),
    path('book/', AppointmentBookingView.as_view(), name='appointment-book'),
    path('dashboard/', ClinicianDashboardView.as_view(), name='clinician-dashboard'),
]