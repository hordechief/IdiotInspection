from django.conf import settings
from django.urls import include, re_path
from django.contrib import admin

# from .dashboard import DashboardViewSINO, sinohome

from .views import (
    DailyInspectionListView,
    DailyInspectionUpdateView,
    DailyInspectionDetailView,
    DailyInspectionCreateView,
    DailyInspectionDeleteView,
    DailyInspectionStatView,

    # LineChartJSONView,
    # OverdueChartJSONView,
    # LastsChartJSONView,
    # CompareChartJSONView,
    # DashboardViewDailyInspection,
)

urlpatterns = [
    # re_path(r'^$', sinohome, name='sinohome'),
    # re_path(r'^dashboard/$', DashboardViewSINO, name='dashboard'),

    re_path(r'^$', DailyInspectionListView.as_view(), name='dailyinspection_list'),
    re_path(r'^create$', DailyInspectionCreateView.as_view(), name='dailyinspection_create'),
    re_path(r'^(?P<pk>\d+)/$', DailyInspectionDetailView.as_view(), name='dailyinspection_detail'),  
    re_path(r'^(?P<pk>\d+)/update/$', DailyInspectionUpdateView.as_view(), name='dailyinspection_update'),
    re_path(r'^(?P<pk>\d+)/delete/$', DailyInspectionDeleteView.as_view(), name='dailyinspection_delete'),
    re_path(r'^api/', include(("daily_inspection.api.urls",'daily_inspection'), namespace="dailyinspection-api")),
    # re_path(r'^stat$', DailyInspectionStatView.as_view(), name='daily_inspection_stat'),   
    # re_path(r'^linechartjason/$', LineChartJSONView.as_view(), name='line_chart_json'),   
    # re_path(r'^linechartjasonoverdue$', OverdueChartJSONView.as_view(), name='line_chart_json_overdue'),   
    # re_path(r'^linechartjasonlasts$', LastsChartJSONView.as_view(), name='line_chart_json_lasts'),   
    # re_path(r'^linechartjasoncompare$', CompareChartJSONView.as_view(), name='line_chart_json_compare'),   
    # re_path(r'^dashboardview/api/dailyinspection/$', DashboardViewDailyInspection.as_view()),   
]