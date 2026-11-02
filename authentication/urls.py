from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from authentication.views import AuditedTokenObtainPairView
from authentication.mfa_views import MFAEnrollmentView, MFAConfirmView, MFADisableView
from authentication.jwt import MFARefreshSerializer
from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    rate = '10/minute'

urlpatterns = [
    # JWT endpoints (these come from SimpleJWT)
    path('login/', AuditedTokenObtainPairView.as_view(throttle_classes=[LoginThrottle]), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(serializer_class=MFARefreshSerializer), name='token_refresh'),
    path('mfa/enroll/', MFAEnrollmentView.as_view(), name='mfa-enroll'),
    path('mfa/confirm/', MFAConfirmView.as_view(), name='mfa-confirm'),
    path('mfa/disable/', MFADisableView.as_view(), name='mfa-disable'),
]
