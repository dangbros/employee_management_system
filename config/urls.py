from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("attendance/", include("attendance.urls")),
    path("leaves/", include("leaves.urls")),
]
