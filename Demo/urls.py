
from django.contrib import admin
from django.urls import path
from core.views import train_and_match

urlpatterns = [
    path("admin/", admin.site.urls),
    path("get_photo/", train_and_match,name="get_photo"),
]
