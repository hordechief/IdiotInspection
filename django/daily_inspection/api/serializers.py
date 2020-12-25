from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField

from ..models import DailyInspection 

class DailyInspectionSerializer(serializers.ModelSerializer):
    # id = SerializerMethodField()
    # url = daily_inspection_detail_url

    class Meta:
        model = DailyInspection
        fields = [
            # "url",
            "id",
            "category",
            "inspection_content",
            'impact',
            'rectification_measures',
            'rectification_status',
            'owner',
            'inspector',
            'due_date',
            'created',
            'updated',
            "completed_time",
            "image_before",
            'image_after',
            'location'
        ]

    # def get_id(self, obj):
    #     return obj.get_absolute_url()

class DailyInspectionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyInspection
        fields = [
            # "id",
            "category",
            "inspection_content",
            'impact',
            'rectification_measures',
            'rectification_status',
            'owner',
            'inspector',
            'due_date',
            # 'created',
            # 'updated',
            # "completed_time",
            # "image_before",
            # 'image_after',
            'location'
        ]
