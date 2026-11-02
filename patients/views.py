from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import PatientProfileSerializer, PatientAccountRegistrationSerializer
from .models import Patient
from authentication.models import User
from audit_logs.utils import log_action


class PatientRegistrationView(generics.CreateAPIView):
    """
    Register a new patient (HCRM-F-001)
    AC-F-001: Patient account and profile creation
    """
    serializer_class = PatientAccountRegistrationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        patient = serializer.save()

        # Log action
        log_action(
            user=patient.user,
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
        # Try to get patient profile, return user info if patient doesn't exist
        try:
            return Patient.objects.get(user=self.request.user)
        except Patient.DoesNotExist:
            # Return user data instead
            return None
    
    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to handle missing patient profile"""
        patient = self.get_object()
        
        if patient:
            serializer = self.get_serializer(patient)
            data = serializer.data
            # Add user ID for appointment booking
            data['id'] = patient.id  # This is the Patient model ID
            data['user_id'] = request.user.id  # This is the User model ID
            data['role'] = request.user.role
            return Response(data)
        else:
            # Return basic user info
            user = request.user
            return Response({
                'user_email': user.email,
                'user_name': user.get_full_name(),
                'role': user.role,
                'username': user.username,
                'id': user.id,  # User ID
                'user_id': user.id
            })
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        
        # Log action
        patient = self.get_object()
        if patient:
            log_action(
                user=request.user,
                action='PROFILE_UPDATED',
                details=f"Patient {patient.patient_id} updated profile"
            )
        
        return response
