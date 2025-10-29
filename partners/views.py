from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PartnerSerializer


class MyListAPIView(APIView):
    def post(self, request):
        serializer = PartnerSerializer(data=request.data)
        if serializer.is_valid():
            names_list = serializer.validated_data['names']
            return Response({"received_names": names_list}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
