from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from partners.services import add_new_record
from partners.tasks import insert_listing
from .serializers import PartnerSerializer


class MyListAPIView(APIView):
    def post(self, request):
        serializer = PartnerSerializer(data=request.data)
        if serializer.is_valid():
            batches = serializer.validated_data['batches']
            add_new_record(batches)
            return Response(status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        insert_listing()
        return Response(status=status.HTTP_200_OK)

    def get(self, request):
        pass
        
