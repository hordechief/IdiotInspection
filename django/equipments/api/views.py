from rest_framework import viewsets
from .serializers import EquipmentSerializer
from equipments.models import Equipment
from rest_framework.views import APIView

class ListEquipments(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """
    #authentication_classes = [authentication.TokenAuthentication]
    #permission_classes = [permissions.IsAdminUser]

    def get(self, request, format=None):
        ii
        equips = Equipment.objects.all()
        serializer = EquipmentSerializer(equips, many=True)
        return response(serializer.data)
        """
        Return a list of all equipments.
        """
        equipmentnames = [equip.name.decode('utf-8').strip() for equip in Equipment.objects.all()]
        return Response(usernames)


class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all().order_by('name')
    serializer_class = EquipmentSerializer
