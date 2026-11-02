from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from notifications.models import ReminderJob


class ReminderJobSerializer(serializers.ModelSerializer):
    appointment_id = serializers.CharField(source='appointment.appointment_id', read_only=True)

    class Meta:
        model = ReminderJob
        fields = ['id', 'appointment_id', 'due_at', 'state', 'attempts', 'last_error', 'sent_at', 'updated_at']


class FailedReminderListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReminderJobSerializer
    queryset = ReminderJob.objects.filter(state='FAILED').select_related('appointment').order_by('-updated_at')

    def list(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({'detail': 'Admin access required.'}, status=403)
        return super().list(request, *args, **kwargs)
