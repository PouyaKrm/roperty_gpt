from rest_framework import serializers

class PartnerSerializer(serializers.Serializer):
    names = serializers.ListField(
        child=serializers.CharField(),  
        allow_empty=False              
    )
