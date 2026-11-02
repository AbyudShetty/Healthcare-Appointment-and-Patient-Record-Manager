from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Custom User model with RBAC (HCRM-SR-003)"""
    
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('CLINICIAN', 'Clinician'),
        ('ADMIN', 'Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PATIENT')
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    mfa_enabled = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_users'
        
    def __str__(self):
        return f"{self.username} ({self.role})"
