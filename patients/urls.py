from django.urls import path
from patients.views import PatientRegistrationView, PatientProfileUpdateView

urlpatterns = [
    path('register/', PatientRegistrationView.as_view(), name='patient-register'),
    path('profile/', PatientProfileUpdateView.as_view(), name='patient-profile'),
]
