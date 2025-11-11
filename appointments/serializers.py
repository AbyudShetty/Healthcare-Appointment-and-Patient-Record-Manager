from rest_framework import serializers
from authentication.models import User
from appointments.models import ClinicianSchedule, Appointment

class ClinicianSearchSerializer(serializers.ModelSerializer):
    """Serializer for clinician search results"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']


class ClinicianAvailabilitySerializer(serializers.ModelSerializer):
    """Serializer for clinician availability"""
    clinician_name = serializers.CharField(source='clinician.get_full_name', read_only=True)
    
    class Meta:
        model = ClinicianSchedule
        fields = ['id', 'clinician_name', 'date', 'start_time', 'end_time', 'is_available']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for appointments"""
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    clinician_name = serializers.CharField(source='clinician.get_full_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['appointment_id', 'patient', 'patient_name', 'clinician', 
                  'clinician_name', 'appointment_date', 'appointment_time', 
                  'duration_minutes', 'reason_for_visit', 'status']
        read_only_fields = ['appointment_id', 'patient_name', 'clinician_name']