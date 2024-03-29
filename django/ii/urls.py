"""ii URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin

from django.urls import path, include
from django.conf.urls.static import static
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import cv2
import base64
import os
import numpy as np


@csrf_exempt
def test(request):
  print(request.POST)
  img_str = request.POST.get("image")
  filename = request.POST.get("filename")
  #print(img_str)
  img_decode_ = img_str.encode('ascii')  # ascii编码
  img_decode = base64.b64decode(img_decode_)  # base64解码
  img_np = np.frombuffer(img_decode, np.uint8)  # 从byte数据读取为np.array形式
  img = cv2.imdecode(img_np, cv2.COLOR_RGB2BGR)  # 转为OpenCV形式
  fullfilename = os.path.join(settings.MEDIA_ROOT,"mci",filename)
  print(fullfilename)
  cv2.imwrite(fullfilename, img, [int(cv2.IMWRITE_PNG_COMPRESSION), 0])
  cv2.imshow('img', img)
  #cv2.imshow('img', image1)
  cv2.waitKey()
  cv2.destroyAllWindows()

  return HttpResponse(b"OK response")

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'is_staff']

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

from equipments.api.views import EquipmentViewSet
router.register(r'equips', EquipmentViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('registration.backends.default.urls')),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(r'equip/', include('equipments.urls')),
    path(r'di/', include('daily_inspection.urls')),
    path(r'test', test),
]

urlpatterns += staticfiles_urlpatterns()
# urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)