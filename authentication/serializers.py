from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from authentication.mfa import consume_code


class SafeTokenObtainPairSerializer(TokenObtainPairSerializer):
    mfa_code = serializers.CharField(required=False, write_only=True, trim_whitespace=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['auth_version'] = user.auth_version
        if user.mfa_enabled:
            token['mfa_device_id'] = getattr(getattr(user, 'mfa_device', None), 'pk', None)
        return token

    def validate(self, attrs):
        code = attrs.pop('mfa_code', '')
        data = super().validate(attrs)
        if self.user.mfa_enabled:
            valid, _ = consume_code(self.user.pk, code)
            if not valid:
                raise AuthenticationFailed('Invalid credentials or authentication code.')
        return data
