from rest_framework import viewsets
from .serializers import EquipmentSerializer
from equipments.models import Equipment
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

class ListEquipments(ListAPIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    #authentication_classes = [authentication.TokenAuthentication]
    #permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        return Equipment.objects.all()

    def get(self, request, format=None):
        equips = Equipment.objects.all()
        serializer = EquipmentSerializer(equips, many=True)
        return Response(serializer.data)
        """
        Return a list of all equipments.
        """
        equipmentnames = [equip.name.decode('utf-8').strip() for equip in Equipment.objects.all()]
        return Response(usernames)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all().order_by('name')
    serializer_class = EquipmentSerializer
