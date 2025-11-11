from django.urls import path
from .views import PatientVolumeReportView

urlpatterns = [
    path('patient-volume/', PatientVolumeReportView.as_view(), name='patient-volume'),
]