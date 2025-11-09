# electronic_records/views.py
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# SimpleJWT auth so "Authorization: Bearer <access_token>" is honored
from rest_framework_simplejwt.authentication import JWTAuthentication

from patients.models import Patient
from electronic_records.models import PatientRecord
from electronic_records.serializers import PatientRecordSerializer


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
