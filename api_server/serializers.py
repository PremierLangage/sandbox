from rest_framework import serializers
from .models import FrozenResource

class FrozenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrozenResource
        fields = ['hash', 'data', 'parent']