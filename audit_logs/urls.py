from django.urls import path
from audit_logs.admin_views import AdminLogsView

urlpatterns = [
    path('', AdminLogsView.as_view(), name='admin-logs-list'),
]