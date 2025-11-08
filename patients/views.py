from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import PatientProfileSerializer
from .models import Patient
from authentication.models import User
from audit_logs.utils import log_action


class PatientRegistrationView(generics.CreateAPIView):
    """
    Register a new patient (HCRM-F-001)
    AC-F-001: Patient account and profile creation
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Create a user and link to a new patient profile
        user_data = self.request.data.get("user", {})
        username = user_data.get("username")
        email = user_data.get("email")
        password = user_data.get("password")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role="PATIENT"
        )

        patient = serializer.save(user=user)

        # Log action
        log_action(
            user=user,
            action="PATIENT_REGISTERED",
            details=f"Patient {patient.patient_id} registered"
        )

        return patient


class PatientProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Update patient profile (HCRM-F-002)
    AC-F-002: Changes reflected in patient record
    """
    serializer_class = PatientProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return Patient.objects.get(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        # Log action
        log_action(
            user=request.user,
            action='PROFILE_UPDATED',
            details=f"Patient {self.get_object().patient_id} updated profile"
        )
        
        return response
