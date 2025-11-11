from django.db import models
from django.utils import timezone

class PatientVolumeReport(models.Model):
    """Daily patient volume report"""
    report_date = models.DateField(unique=True)
    total_appointments = models.IntegerField(default=0)
    completed_appointments = models.IntegerField(default=0)
    cancelled_appointments = models.IntegerField(default=0)
    no_show_appointments = models.IntegerField(default=0)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('authentication.User', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-report_date']
    
    def __str__(self):
        return f"Report for {self.report_date}"