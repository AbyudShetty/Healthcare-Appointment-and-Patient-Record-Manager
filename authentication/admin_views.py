from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from authentication.models import User
from rest_framework import serializers


class UserListSerializer(serializers.ModelSerializer):
    """Simple serializer for user list"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active']


class AdminUserListView(generics.ListAPIView):
    """
    Admin endpoint to list all users
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only allow admin users
        if self.request.user.role != 'ADMIN':
            return User.objects.none()
        return User.objects.all().order_by('-date_joined')