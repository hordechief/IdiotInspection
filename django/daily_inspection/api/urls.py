from django.urls import re_path, path, include

from daily_inspection.api.views import (
    DailyInspectionListAPIView,
    DailyInspectionDetailAPIView,
    DailyInspectionUpdateAPIView,
    DailyInspectionDeleteAPIView,
    DailyInspectionCreateAPIView
    )


urlpatterns = [
    re_path(r'^$', DailyInspectionListAPIView.as_view(), name="list"),
    re_path(r'^(?P<pk>\d+)/$', DailyInspectionDetailAPIView.as_view(), name="detail"),
    re_path(r'^(?P<pk>\d+)/update$', DailyInspectionUpdateAPIView.as_view(), name="update"),
    re_path(r'^(?P<pk>\d+)/delete$', DailyInspectionDeleteAPIView.as_view(), name="delete"),
    re_path(r'^create/$', DailyInspectionCreateAPIView.as_view(), name="create"),

]