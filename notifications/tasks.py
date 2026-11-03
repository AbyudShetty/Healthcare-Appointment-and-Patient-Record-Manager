from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from appointments.models import Appointment

@shared_task
def schedule_appointment_reminder(appointment_id):
    """
    Send appointment reminder 24 hours before (HCRM-F-006)
    AC-F-006: SMS and email reminder sent 24 hours before appointment
    """
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        if appointment.status != 'SCHEDULED':
            return f"Reminder skipped for {appointment.appointment_id}: appointment is {appointment.status}"
        
        patient_email = appointment.patient.user.email
        if not patient_email:
            raise ValueError('Appointment has no patient email address')
        
        send_mail(
            subject='Appointment Reminder',
            message=f"""
            Dear {appointment.patient.user.get_full_name()},
            
            This is a reminder for your appointment:
            
            Date: {appointment.appointment_date}
            Time: {appointment.appointment_time}
            Doctor: Dr. {appointment.clinician.get_full_name()}
            
            Please arrive 10 minutes early.
            
            Best regards,
            HCRM Team
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[patient_email],
            fail_silently=False,
        )
        
        return f"Reminder sent for appointment {appointment.appointment_id}"
    
    except Appointment.DoesNotExist:
        return f"Appointment {appointment_id} not found"
