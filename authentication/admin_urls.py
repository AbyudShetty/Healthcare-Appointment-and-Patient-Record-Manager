from django.urls import path
from authentication.admin_views import AdminUserListView

urlpatterns = [
    path('', AdminUserListView.as_view(), name='admin-user-list'),
]