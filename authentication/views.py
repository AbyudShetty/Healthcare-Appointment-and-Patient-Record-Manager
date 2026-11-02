from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView

from audit_logs.utils import log_action
from authentication.models import User
from authentication.serializers import SafeTokenObtainPairSerializer


class AuditedTokenObtainPairView(TokenObtainPairView):
    serializer_class = SafeTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        user = User.objects.filter(username=username).first() if isinstance(username, str) else None
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            log_action(user=user, action='LOGIN_FAILED', details='Authentication failed',
                       ip_address=request.META.get('REMOTE_ADDR'))
            raise
        log_action(user=user, action='LOGIN_SUCCEEDED', details='Authentication succeeded',
                   ip_address=request.META.get('REMOTE_ADDR'))
        return response
