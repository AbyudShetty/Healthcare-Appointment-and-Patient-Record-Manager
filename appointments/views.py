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
    AppointmentSerializer,
    ClinicianDashboardSerializer
)
from datetime import datetime
from datetime import date

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

class AppointmentBookingView(generics.CreateAPIView):
    """
    Book a new appointment (HCRM-F-005)
    AC-F-005: Appointment created and visible on both patient and clinician calendars
    Transaction time must be ≤10s (HCRM-NF-001)
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if slot is still available
        clinician_id = serializer.validated_data['clinician'].id
        appointment_date = serializer.validated_data['appointment_date']
        appointment_time = serializer.validated_data['appointment_time']
        
        # Check for conflicts
        conflict = Appointment.objects.filter(
            clinician_id=clinician_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='SCHEDULED'
        ).exists()
        
        if conflict:
            return Response(
                {'error': 'This time slot is no longer available'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Create appointment
        appointment = serializer.save()
        
        # Log action
        from audit_logs.utils import log_action
        log_action(
            user=request.user,
            action='APPOINTMENT_BOOKED',
            details=f"Appointment {appointment.appointment_id} booked"
        )
        
        # Trigger reminder notification (async task)
        from notifications.tasks import schedule_appointment_reminder
        schedule_appointment_reminder.delay(appointment.id)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class ClinicianDashboardView(APIView):
    """
    Display clinician's daily schedule (F-007)
    AC-F-007: Shows patient name, time, and reason for visit
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Ensure user is a clinician
        if request.user.role != 'CLINICIAN':
            return Response(
                {'error': 'Only clinicians can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get date from query param or use today
        date_str = request.query_params.get('date', date.today().strftime('%Y-%m-%d'))
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get appointments for this clinician on target date
        appointments = Appointment.objects.filter(
            clinician=request.user,
            appointment_date=target_date
        ).select_related('patient__user').order_by('appointment_time')
        
        serializer = ClinicianDashboardSerializer(appointments, many=True)
        
        return Response({
            'date': target_date,
            'total_appointments': appointments.count(),
            'appointments': serializer.data
        })    