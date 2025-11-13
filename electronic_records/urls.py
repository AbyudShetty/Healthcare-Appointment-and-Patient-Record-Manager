# electronic_records/urls.py
from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny  # 👈 added

from electronic_records.views import SecureHistoryView  # existing import
from electronic_records.views import SecureHistoryView, QuickRecordCreateView


class RecordsHealthCheckView(APIView):
    """
    Simple public endpoint to confirm the Electronic Records API is live.
    Does NOT require authentication.
    """
    permission_classes = [AllowAny]  # 👈 allows public access

    def get(self, request):
        return Response({"message": "Electronic Records endpoint is live!"})


urlpatterns = [
    path("health/", RecordsHealthCheckView.as_view(), name="records-health"),
    # Secure history endpoint: GET /api/v1/records/<patient_id>/history/
    path("<str:patient_id>/history/", SecureHistoryView.as_view(), name="secure-history"),
    path("quick-create/", QuickRecordCreateView.as_view(), name="record-quick-create"),
]
