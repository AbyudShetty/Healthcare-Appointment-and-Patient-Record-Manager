import io
from datetime import timedelta

import pyotp
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from audit_logs.utils import log_action
from authentication.mfa import consume_code
from authentication.models import MFADevice, User
from electronic_records.encryption import encrypt


class MFAThrottle(UserRateThrottle):
    rate = '10/minute'


class MFAEnrollmentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MFAThrottle]

    def post(self, request):
        if not request.user.check_password(request.data.get('password', '')):
            return Response({'detail': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            if user.mfa_enabled:
                return Response({'detail': 'MFA is already enabled.'}, status=status.HTTP_400_BAD_REQUEST)
            device = MFADevice.objects.select_for_update().filter(user=user).first()
            if device and device.locked_until and device.locked_until > timezone.now():
                return Response({'detail': 'Try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            secret = pyotp.random_base32()
            MFADevice.objects.update_or_create(user=user, defaults={
                'secret_encrypted': encrypt(secret), 'pending_expires_at': timezone.now() + timedelta(minutes=10),
                'last_counter': -1, 'recovery_hashes': [],
            })
        uri = pyotp.TOTP(secret).provisioning_uri(name=user.username, issuer_name='HCRM')
        import qrcode
        import qrcode.image.svg
        image = qrcode.make(uri, image_factory=qrcode.image.svg.SvgPathImage)
        output = io.BytesIO()
        image.save(output)
        response = Response({'secret': secret, 'qr_svg': output.getvalue().decode('utf-8')})
        response['Cache-Control'] = 'no-store'
        return response


class MFAConfirmView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MFAThrottle]

    def post(self, request):
        valid, codes = consume_code(request.user.pk, request.data.get('code', ''), enrollment=True)
        if not valid:
            return Response({'detail': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)
        log_action(user=request.user, action='MFA_ENABLED', details='MFA enabled')
        response = Response({'recovery_codes': codes})
        response['Cache-Control'] = 'no-store'
        return response


class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [MFAThrottle]

    def post(self, request):
        if not request.user.check_password(request.data.get('password', '')):
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        valid, _ = consume_code(request.user.pk, request.data.get('code', ''))
        if not valid:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            user.mfa_enabled = False
            user.auth_version += 1
            user.save(update_fields=['mfa_enabled', 'auth_version'])
            MFADevice.objects.filter(user=user).delete()
            log_action(user=user, action='MFA_DISABLED', details='MFA disabled')
        return Response({'detail': 'MFA disabled.'})
