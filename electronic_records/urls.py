from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView


class RecordsHealthCheckView(APIView):
    def get(self, request):
        return Response({"message": "Electronic Records endpoint is live!"})


urlpatterns = [
    path('health/', RecordsHealthCheckView.as_view(), name='records-health'),
]
