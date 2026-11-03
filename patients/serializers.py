from rest_framework import serializers
from authentication.models import User
from patients.models import Patient
from django.db import transaction

class PatientRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for patient registration (HCRM-F-001)"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name', 'phone_number', 'date_of_birth']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            **validated_data,
            role='PATIENT'
        )
        user.set_password(password)
        user.save()
        
        # Create patient profile
        Patient.objects.create(user=user)
        
        return user

class PatientProfileSerializer(serializers.ModelSerializer):
    """Serializer for patient profile"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Patient
        fields = ['patient_id', 'user_email', 'user_name', 'address', 
                  'emergency_contact', 'blood_group', 'allergies']


class RegistrationUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)
    password_confirm = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number', 'date_of_birth']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs


class PatientAccountRegistrationSerializer(PatientProfileSerializer):
    user = RegistrationUserSerializer(write_only=True)

    class Meta(PatientProfileSerializer.Meta):
        fields = ['user'] + PatientProfileSerializer.Meta.fields

    @transaction.atomic
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data.pop('password_confirm')
        password = user_data.pop('password')
        user = User.objects.create_user(password=password, role='PATIENT', **user_data)
        return Patient.objects.create(user=user, **validated_data)
