from django.urls import include, re_path
from django.http import JsonResponse


def home(request):
    return JsonResponse({"message": "Hello Django!"})


urlpatterns = [
    re_path(r'^$', home),
]
