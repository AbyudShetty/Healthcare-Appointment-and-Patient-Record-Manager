# electronic_records/serializers.py
from rest_framework import serializers
from electronic_records.models import PatientRecord, ClinicalNote

# Use the real decrypt helper (make sure electronic_records/utils.py exists)
from electronic_records.utils import decrypt_field as decrypt_field_maybe


class ClinicalNoteSerializer(serializers.ModelSerializer):
    # Read the actual DB column and expose as `note_content`
    note_content = serializers.CharField(source='note_content_encrypted', read_only=True)
    decrypted_note = serializers.SerializerMethodField(read_only=True)

    # We'll compute a friendly clinician name with fallback
    clinician = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ClinicalNote
        fields = ['id', 'clinician', 'note_content', 'decrypted_note', 'created_at']

    def get_decrypted_note(self, obj):
        return decrypt_field_maybe(obj.note_content_encrypted)

    def get_clinician(self, obj):
        user = getattr(obj, 'clinician', None)
        if not user:
            return ""
        # Prefer full name if set, otherwise username, then email
        full = (user.get_full_name() or "").strip()
        if full:
            return full
        if getattr(user, 'username', None):
            return user.username
        if getattr(user, 'email', None):
            return user.email
        return "Unknown clinician"


class PatientRecordSerializer(serializers.ModelSerializer):
    # Your model exposes `clinical_notes` as the reverse relation
    clinical_notes = ClinicalNoteSerializer(many=True, read_only=True)

    medical_history = serializers.CharField(read_only=True)
    diagnoses = serializers.CharField(read_only=True)
    medications = serializers.CharField(read_only=True)

    class Meta:
        model = PatientRecord
        fields = [
            'id',
            'medical_history',
            'diagnoses',
            'medications',
            'clinical_notes',
            'created_at',
            'updated_at',
        ]
