from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.my_leaves, name="my_leaves"),
    path("hr/", views.hr_leaves, name="hr_leaves"),
    path("hr/<int:pk>/approve/", views.approve_leave, name="approve_leave"),
    path("hr/<int:pk>/reject/", views.reject_leave, name="reject_leave"),
]
