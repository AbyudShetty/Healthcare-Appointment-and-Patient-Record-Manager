from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from authentication.serializers import SafeTokenObtainPairSerializer

urlpatterns = [
    # JWT endpoints (these come from SimpleJWT)
    path('login/', TokenObtainPairView.as_view(serializer_class=SafeTokenObtainPairSerializer), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
