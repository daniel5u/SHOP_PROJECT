from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from agent.agent import run_agent
from .serializers import AgentChatSerializer

class AgentChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AgentChatSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user_info_dict = {
            "username": user.username,
            "phone": user.phone,
            "role": user.role,
            "default_address": user.default_address,
            "uuid_id": user.uuid_id,
        }
        message = serializer.validated_data["message"]

        result = run_agent(user_info_dict, message)
        return Response({"reply": result}, status=status.HTTP_200_OK)
