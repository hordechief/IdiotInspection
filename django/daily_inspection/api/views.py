from rest_framework.generics import (
    ListAPIView, 
    RetrieveAPIView,
    UpdateAPIView,
    RetrieveUpdateAPIView,
    DestroyAPIView,
    CreateAPIView
    )
from rest_framework.filters import (
    SearchFilter,
    OrderingFilter,
    )

from rest_framework.permissions import(
    AllowAny,
    IsAuthenticated,
    IsAdminUser,
    # IsAuthenticatedOrReadonly,
    )

from django_filters.rest_framework import DjangoFilterBackend

from django.db.models.query import Q

from daily_inspection.models import DailyInspection 
from daily_inspection.api.serializers import DailyInspectionSerializer, DailyInspectionCreateSerializer

# from ..views import DailyInspectionFilter, DailyInspectionListView

class DailyInspectionListAPIView(ListAPIView):
    # queryset = DailyInspection.objects.all()
    serializer_class = DailyInspectionSerializer
    # filter_backends = (DjangoFilterBackend,)
    # filter_backends = [SearchFilter, OrderingFilter]
    ordering_fields  = ['-created', ]
    search_fields = ('inspection_content', 'location')
    # filter_class = DailyInspectionFilter

    queryset = DailyInspection.objects.all()

    # def further_filter(self, object_list):
    #     if self.request.GET.get('keyword', None) and self.request.GET.get('username', None):
    #         keyword = self.request.GET['keyword']
    #         username = self.request.GET['username']
    #         objs = TriggerScrapRecord.objects.filter(username=self.request.user.username)
    #         for _ in objs:
    #             if keyword.lower() == _.keyword.lower():
    #                 object_list = _.job_entries.all()
    #                 break
    #     return object_list

    # def get_queryset(self, *args, **kwargs):
    #     queryset = DailyInspection.objects.all()
    #     queryset_list = self.filter_class(self.request.GET, queryset).qs
    #     queryset_list = DailyInspectionListView.further_filter(self.request, queryset_list)
    #     return queryset_list

class DailyInspectionDetailAPIView(RetrieveAPIView):
    lookup_field = "pk"

    queryset = DailyInspection.objects.all()
    serializer_class = DailyInspectionSerializer        


class DailyInspectionUpdateAPIView(RetrieveUpdateAPIView):
    queryset = DailyInspection.objects.all()
    serializer_class = DailyInspectionSerializer
    lookup_field = "pk"

    permission_classes = [AllowAny] 

class DailyInspectionDeleteAPIView(DestroyAPIView):
    queryset = DailyInspection.objects.all()
    serializer_class = DailyInspectionSerializer
    lookup_field = "pk"    

class DailyInspectionCreateAPIView(CreateAPIView):
    queryset = DailyInspection.objects.all()
    serializer_class = DailyInspectionCreateSerializer   

    permission_classes = [IsAuthenticated] 

