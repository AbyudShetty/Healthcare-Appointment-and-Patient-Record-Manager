from rest_framework.response import Response
from rest_framework.views import APIView

class AppointmentHealthCheckView(APIView):
    def get(self, request):
        return Response({"message": "Appointments endpoint is live!"})
