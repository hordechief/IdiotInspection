from django.urls import path
from rest_framework.response import Response
from rest_framework import authentication, permissions
from equipments.models import Equipment
from equipments.api.views import (EquipmentViewSet, ListEquipments)
from django.urls import path, include

urlpatterns = [
    path('api/', ListEquipments.as_view(),)
]
