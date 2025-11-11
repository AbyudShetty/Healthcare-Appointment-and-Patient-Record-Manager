from rest_framework import serializers
from .models import PatientVolumeReport

class PatientVolumeReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    
    class Meta:
        model = PatientVolumeReport
        fields = ['id', 'report_date', 'total_appointments', 
                  'completed_appointments', 'cancelled_appointments',
                  'no_show_appointments', 'generated_at', 'generated_by_name']