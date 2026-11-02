from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.db import transaction
from django.utils import timezone
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
from datetime import timedelta
from patients   .models import Patient


class AppointmentHealthCheckView(APIView):
    def get(self, request):
        return Response({"message": "Appointments endpoint is live!"})

class ClinicianSearchView(generics.ListAPIView):
    """
    Search clinicians by specialty or name (HCRM-F-003)
    """
    serializer_class = ClinicianSearchSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # 👈 Disable pagination so tests get a list

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
            queryset = queryset.filter(specialty__icontains=specialty)
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

        booked_slots = list(
            Appointment.objects.filter(
                clinician_id=clinician_id,
                appointment_date=date_obj,
                status__iexact='SCHEDULED'
            ).values_list('appointment_time', 'duration_minutes')
        )

        available_slots = []
        for slot in serializer.data:
            slot_start = datetime.combine(date_obj, datetime.strptime(slot['start_time'], "%H:%M:%S").time())
            slot_end = datetime.combine(date_obj, datetime.strptime(slot['end_time'], "%H:%M:%S").time())
            if not any(slot_start < datetime.combine(date_obj, t) + timedelta(minutes=d)
                       and datetime.combine(date_obj, t) < slot_end for t, d in booked_slots):
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
        if request.user.role != 'PATIENT' or serializer.validated_data['patient'].user_id != request.user.id:
            return Response({'error': 'Patients may only book their own appointments'}, status=status.HTTP_403_FORBIDDEN)
        if serializer.validated_data['clinician'].role != 'CLINICIAN':
            return Response({'error': 'Selected user is not a clinician'}, status=status.HTTP_400_BAD_REQUEST)
        if serializer.validated_data.get('status', 'SCHEDULED') != 'SCHEDULED':
            return Response({'error': 'New appointments must be scheduled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if slot is still available
        clinician_id = serializer.validated_data['clinician'].id
        appointment_date = serializer.validated_data['appointment_date']
        appointment_time = serializer.validated_data['appointment_time']
        
        duration = serializer.validated_data.get('duration_minutes', 30)
        start = datetime.combine(appointment_date, appointment_time)
        end = start + timedelta(minutes=duration)
        if duration <= 0 or end.date() != appointment_date or timezone.make_aware(start) <= timezone.now():
            return Response({'error': 'Choose a future time and a valid duration'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Serialize all booking requests for a clinician, including overlapping slots.
            User.objects.select_for_update().get(pk=clinician_id)
            schedule = ClinicianSchedule.objects.filter(
                clinician_id=clinician_id, date=appointment_date,
                start_time=appointment_time, is_available=True,
            ).first()
            if not schedule or end.time() > schedule.end_time:
                return Response({'error': 'Choose an available schedule slot'}, status=status.HTTP_400_BAD_REQUEST)
            existing = Appointment.objects.filter(
                clinician_id=clinician_id, appointment_date=appointment_date, status='SCHEDULED'
            ).values_list('appointment_time', 'duration_minutes')
            if any(start < datetime.combine(appointment_date, t) + timedelta(minutes=d)
                   and datetime.combine(appointment_date, t) < end for t, d in existing):
                return Response({'error': 'This time slot is no longer available'}, status=status.HTTP_409_CONFLICT)
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
        try:
            reminder_at = timezone.make_aware(datetime.combine(appointment.appointment_date, appointment.appointment_time)) - timedelta(hours=24)
            schedule_appointment_reminder.apply_async(args=[appointment.id], eta=max(reminder_at, timezone.now()))
        except Exception:
            import logging
            logging.getLogger(__name__).exception('Unable to schedule reminder for appointment %s', appointment.appointment_id)
        
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
    

class ClinicianScheduleManagementView(generics.ListCreateAPIView):
    """
    Admin manages clinician schedules (F-011)
    """
    serializer_class = ClinicianAvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'ADMIN':
            return ClinicianSchedule.objects.none()
        
        clinician_id = self.request.query_params.get('clinician_id')
        if clinician_id:
            return ClinicianSchedule.objects.filter(clinician_id=clinician_id)
        return ClinicianSchedule.objects.all()
    
    def create(self, request, *args, **kwargs):
        if self.request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only administrators can manage schedules'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)

class ClinicianScheduleDeleteView(generics.DestroyAPIView):
    """Delete/remove clinician time slots (F-011)"""
    permission_classes = [IsAuthenticated]
    # We query all schedules, but the lookup_field ('pk') in the URL
    # will select the specific one to delete.
    queryset = ClinicianSchedule.objects.all()
    
    def delete(self, request, *args, **kwargs):
        if self.request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only administrators can delete schedules'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().delete(request, *args, **kwargs)   


class AppointmentStatusUpdateView(generics.UpdateAPIView):
    """
    Update appointment status (F-013)
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Appointment.objects.all()
    # We use 'appointment_id' (e.g., "APT000001") as the URL lookup
    lookup_field = 'appointment_id' 
    
    def update(self, request, *args, **kwargs):
        # Check for Admin or Clinician role
        if request.user.role not in ['ADMIN', 'CLINICIAN']:
            return Response(
                {'error': 'Only administrators or clinicians can update status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        appointment = self.get_object()
        if request.user.role == 'CLINICIAN' and appointment.clinician_id != request.user.id:
            return Response({'error': 'You may only update your own appointments'}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        
        # Validate the new status is one of the allowed choices
        if new_status not in ['COMPLETED', 'CANCELLED', 'NO_SHOW']:
            return Response(
                {'error': 'Invalid status. Must be COMPLETED, CANCELLED, or NO_SHOW.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if appointment.status != 'SCHEDULED' and appointment.status != new_status:
            return Response({'error': 'A closed appointment cannot change status'}, status=status.HTTP_409_CONFLICT)
        appointment.status = new_status
        appointment.save()
        
        # Log this action to the audit trail
        from audit_logs.utils import log_action
        log_action(
            user=request.user,
            action='APPOINTMENT_STATUS_UPDATED',
            details=f"Appointment {appointment.appointment_id} marked as {new_status}"
        )
        
        serializer = self.get_serializer(appointment)
        return Response(serializer.data)     
    
class AppointmentListView(generics.ListAPIView):
    """
    List all appointments for the authenticated user
    """
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'PATIENT':
            # Get patient's appointments
            try:
                patient = Patient.objects.get(user=user)
                return Appointment.objects.filter(patient=patient).order_by('-appointment_date', '-appointment_time')
            except Patient.DoesNotExist:
                return Appointment.objects.none()
        elif user.role == 'CLINICIAN':
            # Get clinician's appointments
            return Appointment.objects.filter(clinician=user).order_by('-appointment_date', '-appointment_time')
        elif user.role == 'ADMIN':
            # Admin can see all
            return Appointment.objects.all().order_by('-appointment_date', '-appointment_time')
        
        return Appointment.objects.none()
