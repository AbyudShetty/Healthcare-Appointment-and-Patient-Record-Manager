# electronic_records/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# SimpleJWT auth so "Authorization: Bearer <access_token>" is honored
from rest_framework_simplejwt.authentication import JWTAuthentication

from patients.models import Patient
from electronic_records.models import PatientRecord, ClinicalNote
from electronic_records.serializers import PatientRecordSerializer, ClinicalNoteSerializer

from electronic_records.utils import encrypt_field  
from audit_logs.utils import log_action    
from .models import PatientRecord      

from django.core.files.base import ContentFile
from .models import PatientDocument
from .serializers import PatientDocumentSerializer, PatientDocumentUploadSerializer
from .encryption import encrypt_file, decrypt_file


def _user_is_clinician_or_admin(user):
    """
    Return True for staff/superuser or users with a clinician/admin role.
    Adapt role strings if your project uses different values.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    # built-in Django flags first
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True
    role = getattr(user, "role", None)
    return role in ("CLINICIAN", "ADMIN", "STAFF")


class SecureHistoryView(generics.ListAPIView):
    """
    GET /api/v1/records/<patient_id>/history/
    - Requires Bearer <access_token> (SimpleJWT).
    - Clinicians/Admins can fetch any patient's records.
    - Patient users with role 'PATIENT' can only fetch their own records.
    """
    serializer_class = PatientRecordSerializer

    # Ensure view uses SimpleJWT to interpret Authorization header
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Queryset limited to PatientRecord for the requested patient.
        Returns a QuerySet (may be empty) ordered by created_at desc.
        """
        patient_id = self.kwargs.get("patient_id")
        patient = get_object_or_404(Patient, patient_id=patient_id)
        return PatientRecord.objects.filter(patient=patient).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        """
        Additional authorization logic:
        - Staff / superuser / clinician roles: allowed
        - Patient: allowed only if patient.user == request.user
        - Others: forbidden
        """
        patient_id = self.kwargs.get("patient_id")
        patient = get_object_or_404(Patient, patient_id=patient_id)

        # Authorization
        if _user_is_clinician_or_admin(request.user):
            allowed = True
        else:
            # Check patient self-access
            if getattr(request.user, "role", None) == "PATIENT":
                # patient must be linked to a user object
                if not hasattr(patient, "user") or patient.user != request.user:
                    return Response(
                        {"detail": "Not allowed to view other patients' records."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                allowed = True
            else:
                allowed = False

        if not allowed:
            return Response({"detail": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        # If authorized, return serialized records (ListAPIView handles pagination)
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



class QuickRecordCreateView(generics.CreateAPIView):
    """
    Quick patient record creation (F-008)
    NF-002: Must load/create within <= 5 seconds
    """
    serializer_class = PatientRecordSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Verify clinician role
        if request.user.role not in ['CLINICIAN', 'ADMIN']:
            return Response(
                {'error': 'Only clinicians can create records'},
                status=status.HTTP_403_FORBIDDEN
            )

        patient_id = request.data.get('patient_id')

        # Get patient
        patient = get_object_or_404(Patient, patient_id=patient_id)

        # Create minimal record
        record = PatientRecord.objects.create(
            patient=patient,
            created_by=request.user,
            medical_history_encrypted=encrypt_field(request.data.get('medical_history', '')),
            diagnoses_encrypted=encrypt_field(request.data.get('diagnoses', '')),
            medications_encrypted=encrypt_field(request.data.get('medications', ''))
        )

        # Log action
        from audit_logs.utils import log_action
        log_action(
            user=request.user,
            action='RECORD_CREATED',
            details=f"Record created for patient {patient.patient_id}"
        )

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)




class ClinicalNoteCreateView(generics.CreateAPIView):
    """
    Add clinical notes to patient record (F-009)
    SR-004: Logs all note creation/modification in audit trail
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if request.user.role not in ['CLINICIAN', 'ADMIN']:
            return Response(
                {'error': 'Only clinicians can add notes'},
                status=status.HTTP_403_FORBIDDEN
            )

        record_id = request.data.get('record_id')
        note_content = request.data.get('note_content')

        # Find the patient record to attach the note to
        record = get_object_or_404(PatientRecord, id=record_id)

        # Create note
        # The model's .save() method will handle the encryption
        #
        note = ClinicalNote.objects.create(
            record=record,
            clinician=request.user,
            note_content_encrypted=note_content 
        )

        # Audit log
        from audit_logs.utils import log_action
        log_action(
            user=request.user,
            action='CLINICAL_NOTE_ADDED',
            details=f"Note added to record {record.id} by {request.user.get_full_name()}"
        )

        serializer = self.get_serializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class PatientDocumentUploadView(generics.CreateAPIView):
    """Upload encrypted patient documents (F-014)"""
    serializer_class = PatientDocumentUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        document_type = serializer.validated_data['document_type']
        
        # Get patient
        patient = Patient.objects.get(user=request.user)
        
        # Read and encrypt file
        file_data = file.read()
        encrypted_data = encrypt_file(file_data)
        
        # Save encrypted file
        document = PatientDocument.objects.create(
            patient=patient,
            document_type=document_type,
            original_filename=file.name,
            uploaded_by=request.user,
            file_size_bytes=file.size
        )
        
        document.file_encrypted.save(
            f"encrypted_{file.name}",
            ContentFile(encrypted_data),
            save=True
        )
        
        # Log action
        from audit_logs.utils import log_action
        log_action(
            user=request.user,
            action='DOCUMENT_UPLOADED',
            details=f"Document {file.name} uploaded for patient {patient.patient_id}"
        )
        
        return Response(
            PatientDocumentSerializer(document).data,
            status=status.HTTP_201_CREATED
        )

class PatientDocumentListView(generics.ListAPIView):
    """List patient's documents"""
    serializer_class = PatientDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        patient = Patient.objects.get(user=self.request.user)
        return PatientDocument.objects.filter(patient=patient)