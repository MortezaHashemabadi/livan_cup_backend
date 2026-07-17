from rest_framework import serializers
from .models import PriceTier


class PriceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTier
        fields = ['min_quantity', 'max_quantity', 'unit_price']