from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


class MFAJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        device = getattr(user, 'mfa_device', None)
        if validated_token.get('auth_version', 0) != user.auth_version:
            raise AuthenticationFailed('Session has been revoked.')
        if user.mfa_enabled and (not device or validated_token.get('mfa_device_id') != device.pk):
            raise AuthenticationFailed('MFA authentication is required.')
        return user


class MFARefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        token = RefreshToken(attrs['refresh'])
        user = get_user_model().objects.filter(pk=token.get('user_id'), is_active=True).first()
        device = getattr(user, 'mfa_device', None) if user else None
        if not user or token.get('auth_version', 0) != user.auth_version or (user.mfa_enabled and (not device or token.get('mfa_device_id') != device.pk)):
            raise AuthenticationFailed('MFA authentication is required.')
        return super().validate(attrs)
