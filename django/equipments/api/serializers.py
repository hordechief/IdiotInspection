# serializers.py
from rest_framework import serializers

from equipments.models import Equipment
class EquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipment
        fields = ('name', 'id')

