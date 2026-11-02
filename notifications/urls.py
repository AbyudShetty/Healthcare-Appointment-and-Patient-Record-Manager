from django.urls import path
from notifications.views import FailedReminderListView

urlpatterns = [path('failed/', FailedReminderListView.as_view(), name='failed-reminders')]
