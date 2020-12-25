from django.views.generic.list import ListView
from django.db.models import Q
from chartjs.views.lines import (JSONView, BaseLineChartView)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.utils.translation import ugettext as _
import json

from .models import (
    DailyInspection, 
    )
    
from .mixins import StatMixin    
    
class ChartMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super(ChartMixin, self).get_context_data(*args, **kwargs)
        object_list = context["object_list"]
        data = { 
            'datasets': [{
                # 'label': '# of Votes',
                'data': [object_list.filter(category=category[0]).count() if not object_list is None else 0 for category in DailyInspection.daily_insepction_category],
                'backgroundColor': [
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',
                ]            
            }],

            # These labels appear in the legend and in the tooltips when hovering different arcs
            'labels': [_(category[1]) for category in DailyInspection.daily_insepction_category], # why ugettext in models.py didn't work?
        };
        context["data"] = json.dumps(data)
        
        return context

# https://github.com/novafloss/django-chartjs
class LineChartColorMixin(object):
    def get_context_data(self):
        data = super(LineChartColorMixin, self).get_context_data()
        backgroundColors =[
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',                    
                ]

        borderColors =[
                    'rgba(255, 0, 0, 0.1)',
                    'rgba(0, 255, 0, 0.1)',
                    'rgba(0, 0, 255, 0.1)',
                    'rgba(220, 0, 255, 0.1)',
                    'rgba(0, 220, 255, 0.1)',                    
                ]                

        for i in range(0,len(self.get_providers())):
        #for i, color in enumerate(backgroundColors)
            data['datasets'][i]['backgroundColor'] = backgroundColors[i]
            data['datasets'][i]['borderColor'] = borderColors[i]

        # print data
        return data 

class LineChartJSONView(StatMixin, LineChartColorMixin, BaseLineChartView):
    def get_labels(self):
        """Return labels for the x-axis."""
        return self.get_dates()

    def get_providers(self):
        """Return names of datasets."""
        return self.get_catetory()

    def get_data(self):
        """Return 3 datasets to plot."""
        return self.get_chart_counts()


# var data = {
#     labels : ["January","February","March","April","May","June","July"],
#     datasets : [
#         {
#             fillColor : "rgba(220,220,220,0.5)",
#             strokeColor : "rgba(220,220,220,1)",
#             data : [65,59,90,81,56,55,40]
#         },
#         {
#             fillColor : "rgba(151,187,205,0.5)",
#             strokeColor : "rgba(151,187,205,1)",
#             data : [28,48,40,19,96,27,100]
#         }
#     ]
# }

class OverdueChartJSONView(JSONView):

    def get_context_data(self):
        data = { 
            'datasets': [{
                # 'label': '# of Votes',
                'data': [DailyInspection.objects.filter(rectification_status="uncompleted", due_date__lt=timezone.now(), category=category[0]).count() for category in DailyInspection.daily_insepction_category]\
                if self.request.user.is_staff else \
                    [0 for category in DailyInspection.daily_insepction_category],
                'backgroundColor': [
                    'rgba(255, 0, 0, 0.2)',
                    'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',
                ]            
            }],

            # These labels appear in the legend and in the tooltips when hovering different arcs
            'labels': [category[1] for category in DailyInspection.daily_insepction_category],
        };

        return data

class LastsChartJSONView(LineChartColorMixin, BaseLineChartView):
    def get_time_range(self):
        times =  [timezone.now(), timezone.now() - timedelta(weeks=1)]
        return times
               
    def get_labels(self):
        """Return labels for the x-axis."""
        return [category[1] for category in DailyInspection.daily_insepction_category]

    def get_providers(self):
        """Return names of datasets."""
        providers =  [ "{0}  ~  {1}".format(self.get_time_range()[1].date(), self.get_time_range()[0].date()), ]
        return providers

    def get_data(self):
        data =  [[DailyInspection.objects.filter(category=category[0], created__gte=self.get_time_range()[1]).count()\
                if self.request.user.is_staff else \
                DailyInspection.objects.filter(rectification_status="completed", category=category[0], created__gte=self.get_time_range()[1]).count()\
                     for category in DailyInspection.daily_insepction_category],]
        return data

class CompareChartJSONView(LineChartColorMixin, BaseLineChartView):
    def get_last_times(self):
        #  RuntimeWarning: DateTimeField DailyInspection.created received a naive datetime (2017-12-02 23:59:59) while time zone support is active.
        year = timezone.now().year #time.localtime()[0]
        month = timezone.now().month #time.localtime()[1]        
        return [[month-i or 12, year if month > i else year-1] for i in reversed(range(0,1))]
               
    def get_labels(self):
        """Return labels for the x-axis."""
        return [category[1] for category in DailyInspection.daily_insepction_category]

    def get_providers(self):
        """Return names of datasets."""
        return [            
            "{0}-{1:0>2d}".format(year,month) for month,year in self.get_last_times()
        ]

    def get_data(self):
        data =  [[DailyInspection.objects.filter(category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count() \
                if self.request.user.is_staff else \
                DailyInspection.objects.filter(rectification_status="completed", category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count()\
                    for category in DailyInspection.daily_insepction_category] \
                        for month, year in self.get_last_times()]
        # data =  [[DailyInspection.objects.filter(category=category[0], created__year=year, created__month=month).count() for category in DailyInspection.daily_insepction_category] \
        #             for month, year in self.get_last_times()]     
        # issue for filter "created__month=month" # https://segmentfault.com/q/1010000009037684
        return data


    # function is same base class, color is different , to be improved
    def get_context_data(self):
        data = super(CompareChartJSONView, self).get_context_data()
        backgroundColors =[
                    # 'rgba(255, 0, 0, 0.2)',
                    # 'rgba(0, 255, 0, 0.2)',
                    'rgba(0, 0, 255, 0.2)',
                    'rgba(220, 0, 255, 0.2)',
                    'rgba(0, 220, 255, 0.2)',                    
                ]

        borderColors =[
                    # 'rgba(255, 0, 0, 0.1)',
                    # 'rgba(0, 255, 0, 0.1)',
                    'rgba(0, 0, 255, 0.1)',
                    'rgba(220, 0, 255, 0.1)',
                    'rgba(0, 220, 255, 0.1)',                    
                ]                

        for i in range(0,len(self.get_providers())):
        #for i, color in enumerate(backgroundColors)
            data['datasets'][i]['backgroundColor'] = backgroundColors[i]
            data['datasets'][i]['borderColor'] = borderColors[i]

        return data 

class DashboardViewDailyInspection(APIView):
    authentication_classes = []
    permission_classes = []

    def get_last_times(self):
        year = timezone.now().year #time.localtime()[0]
        return [[i, year] for i in range(1,13)]

    def get(self, request, format=None):
        rows = [[DailyInspection.objects.filter(category=category[0], created__startswith="{0}-{1:0>2d}-".format(year,month)).count() for category in DailyInspection.daily_insepction_category] \
                    for month, year in self.get_last_times()]
        columns = [ (month[0], month[1]) for month in month_choice]
        data = {
                "columns": columns,
                "rows": rows,
        }
        return Response(data)    
