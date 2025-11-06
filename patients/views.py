from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from patients.models import Patient
from patients.serializers import PatientRegistrationSerializer, PatientProfileSerializer
from audit_logs.utils import log_action

class PatientRegistrationView(generics.CreateAPIView):
    """
    API endpoint for patient registration (HCRM-F-001)
    AC-F-001: New patient can create account with required info, unique patient ID assigned
    """
    serializer_class = PatientRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        patient = Patient.objects.get(user=user)
        
        # Log action (HCRM-SR-004)
        log_action(
            user=user,
            action='PATIENT_REGISTERED',
            details=f"New patient registered: {patient.patient_id}"
        )
        
        return Response({
            'message': 'Patient registered successfully',
            'patient_id': patient.patient_id,
            'username': user.username
        }, status=status.HTTP_201_CREATED)