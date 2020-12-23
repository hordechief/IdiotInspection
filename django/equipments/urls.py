from django.urls import path, include

urlpatterns = [
    path('api/', include(("equipments.api.urls",'equipments'),namespace="equip-api")),
]
