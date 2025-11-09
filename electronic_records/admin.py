# electronic_records/admin.py
from django.contrib import admin
from .models import PatientRecord, ClinicalNote

@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('patient__user__username', 'medical_history_encrypted', 'diagnoses_encrypted')

@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'clinician', 'created_at')
    search_fields = ('note_content_encrypted',)
