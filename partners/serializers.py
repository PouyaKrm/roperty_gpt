from rest_framework import serializers

class PartnerSerializer(serializers.Serializer):
    batches = serializers.ListField(
        child=serializers.CharField(),  
        allow_empty=False              
    )
