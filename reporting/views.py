from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from datetime import date, timedelta
from appointments.models import Appointment
from .models import PatientVolumeReport
from .serializers import PatientVolumeReportSerializer
from datetime import date, datetime, timedelta

class PatientVolumeReportView(generics.ListCreateAPIView):
    """
    Generate patient volume report (F-012)
    """
    serializer_class = PatientVolumeReportSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'ADMIN':
            return PatientVolumeReport.objects.none()
        return PatientVolumeReport.objects.all()
    
    def create(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response(
                {'error': 'Only administrators can generate reports'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get date from request or use today
        report_date_str = request.data.get('date', date.today().strftime('%Y-%m-%d'))
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
        
        # Aggregate appointment data
        appointments = Appointment.objects.filter(appointment_date=report_date)
        
        stats = appointments.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='COMPLETED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
            no_show=Count('id', filter=Q(status='NO_SHOW'))
        )
        
        # Create or update report
        report, created = PatientVolumeReport.objects.update_or_create(
            report_date=report_date,
            defaults={
                'total_appointments': stats['total'],
                'completed_appointments': stats['completed'],
                'cancelled_appointments': stats['cancelled'],
                'no_show_appointments': stats['no_show'],
                'generated_by': request.user
            }
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)