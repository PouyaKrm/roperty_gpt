from rest_framework import serializers

class PartnerSerializer(serializers.Serializer):
    batches = serializers.ListField(
        child=serializers.JSONField(),  
        allow_empty=False              
    )

