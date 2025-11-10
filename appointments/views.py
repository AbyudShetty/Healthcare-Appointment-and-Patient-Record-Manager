from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from appointments.models import Appointment, ClinicianSchedule
from authentication.models import User
from appointments.serializers import (
    ClinicianSearchSerializer, 
    ClinicianAvailabilitySerializer,
    AppointmentSerializer
)
from datetime import datetime

class AppointmentHealthCheckView(APIView):
    def get(self, request):
        return Response({"message": "Appointments endpoint is live!"})

class ClinicianSearchView(generics.ListAPIView):
    """
    Search clinicians by specialty or name (HCRM-F-003)
    AC-F-003: Returns list of clinicians matching search criteria
    """
    serializer_class = ClinicianSearchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        specialty = self.request.query_params.get('specialty', '')
        
        queryset = User.objects.filter(role='CLINICIAN')
        
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(username__icontains=query)
            )
        
        if specialty:
            # Assuming specialty is stored in a related profile or extended model
            pass
        
        return queryset

class ClinicianAvailabilityView(generics.ListAPIView):
    """
    Display clinician's available time slots (HCRM-F-004)
    AC-F-004: Accurately displays available slots with real-time update delay ≤5s
    """
    serializer_class = ClinicianAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        clinician_id = self.kwargs.get('clinician_id')
        date = self.request.query_params.get('date')
        
        queryset = ClinicianSchedule.objects.filter(
            clinician_id=clinician_id,
            is_available=True
        )
        
        if date:
            queryset = queryset.filter(date=date)
        
        return queryset

    def list(self, request, *args, **kwargs):
        clinician_id = self.kwargs.get('clinician_id')
        get_object_or_404(User, id=clinician_id, role='CLINICIAN')

        date_str = self.request.query_params.get('date')
        if not date_str:
            return Response({"error": "Missing 'date' parameter"}, status=400)
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        booked_slots = set(
            Appointment.objects.filter(
                clinician_id=clinician_id,
                appointment_date=date_obj,
                status__iexact='SCHEDULED'
            ).values_list('appointment_time', flat=True)
        )

        available_slots = []
        for slot in serializer.data:
            slot_time = datetime.strptime(slot['start_time'], "%H:%M:%S").time()
            if slot_time not in booked_slots:
                available_slots.append(slot)

        return Response(available_slots)