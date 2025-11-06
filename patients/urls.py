from django.urls import path
from patients.views import PatientRegistrationView

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name='patient-register'),
]