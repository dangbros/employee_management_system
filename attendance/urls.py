from django.urls import path

from . import views

urlpatterns = [
    path("me/", views.employee_dashboard, name="employee_dashboard"),
    path("check-in/", views.check_in_view, name="check_in"),
    path("check-out/", views.check_out_view, name="check_out"),
    path("history/", views.history, name="attendance_history"),
    path("hr/", views.hr_dashboard, name="hr_dashboard"),
    path("hr/employee/<int:user_id>/", views.hr_employee_detail, name="hr_employee_detail"),
]
