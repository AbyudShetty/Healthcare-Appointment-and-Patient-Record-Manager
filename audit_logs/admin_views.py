from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from audit_logs.models import AuditLog


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
            return Response({'detail': 'Admin access required'}, status=403)
        
        return self.list(request, *args, **kwargs)
