from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from audit_logs.models import AuditLog
from audit_logs.utils import log_action


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True, allow_null=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'action', 'details', 'ip_address', 'timestamp']


class AdminLogsView(generics.ListAPIView):
    """
    Admin endpoint to view audit logs (stub)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.select_related('user').all()
    
    def get(self, request, *args, **kwargs):
        # Only allow admin users
        if request.user.role != 'ADMIN':
            log_action(user=request.user, action='AUDIT_LOGS_DENIED', details='Audit log access denied',
                       ip_address=request.META.get('REMOTE_ADDR'))
            return Response({'detail': 'Admin access required'}, status=403)
        log_action(user=request.user, action='AUDIT_LOGS_VIEWED', details='Audit logs viewed',
                   ip_address=request.META.get('REMOTE_ADDR'))
        return self.list(request, *args, **kwargs)
