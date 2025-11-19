from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class AdminLogsView(generics.ListAPIView):
    """
    Admin endpoint to view audit logs (stub)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        # Only allow admin users
        if request.user.role != 'ADMIN':
            return Response({'detail': 'Admin access required'}, status=403)
        
        # Return empty array for now - logs feature coming soon
        return Response([])