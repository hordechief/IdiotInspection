from .models import (
    DailyInspection, 
    )
    
class StatMixin(object):

    # ['category']['date']['count']
    # {'people',{'2017-08-01':'0','2017-08-02':'1'}}

    def get_dates(self):
        #dates = list([ ins.created.strftime("%Y-%m-%d") for ins in DailyInspection.objects.order_by('-updated')])        
        dates = list([ ins.get_created_date() for ins in DailyInspection.objects.order_by('-updated')[:30]])
        dates = list(set(dates))
        dates.sort()
        return dates

    def get_dates_value(self):
        dates = list([ ins.created for ins in DailyInspection.objects.order_by('-updated')[:30]])
        dates = list(set(dates))
        dates.sort()
        return dates

    def get_catetory(self):
        categories = list([ ins[1] for ins in DailyInspection.daily_insepction_category])
        return categories

    def get_catetory_value(self):
        categories = list([ ins[0] for ins in DailyInspection.daily_insepction_category])
        return categories

    def get_chart_counts(self):
        counts = []
        dates = self.get_dates()
        categories = self.get_catetory_value()
        for category in categories:
            count  = [DailyInspection.objects.filter(created__range=(\
                            datetime.datetime( datetime.datetime.strptime(date,'%Y-%m-%d').year, datetime.datetime.strptime(date,'%Y-%m-%d').month,datetime.datetime.strptime(date,'%Y-%m-%d').day,0,0,0),\
                            datetime.datetime(datetime.datetime.strptime(date,'%Y-%m-%d').year, datetime.datetime.strptime(date,'%Y-%m-%d').month,datetime.datetime.strptime(date,'%Y-%m-%d').day,23,59,59)))\
                                             .filter(category=category).count() for date in dates ]
            if counts == None:
                counts = [count]
            else:
                counts.append(count)
        return counts


    def get_counters_sorted(self):
        llcounterperdaypercategory = {}
        for category in self.get_catetory():
            #llcounterperdaypercategory.update({category:{}})
            llcounterperdaypercategory[category] = {}
            for date in self.get_dates():
                llcounterperdaypercategory[category].update({date:0})

        return self.get_counters(llcounterperdaypercategory)

    def get_counters(self, llcounterperdaypercategory):
        #llcounterperdaypercategory = {}
        for inspect in DailyInspection.objects.all():
            created = inspect.get_created_date()
            category = inspect.my_get_field_display('category')
            if llcounterperdaypercategory.get(category, None) is None:
                llcounterperdaypercategory.update({category: {created : 1}})
            else:                
                if llcounterperdaypercategory[category].get(created, None):
                    llcounterperdaypercategory[category][created] = llcounterperdaypercategory[category].get(created, None) + 1
                else:
                    llcounterperdaypercategory[category].update({created:1})

        return llcounterperdaypercategory

