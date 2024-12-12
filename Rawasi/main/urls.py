from . import views
from django.urls import path

app_name="main"

urlpatterns=[
    path('',views.home_view,name="home_view"),
    path('about/',views.about_view,name="about_view"),
    path('dashboard/leader/',views.leader_dashboard_view,name="leader_dashboard_view"),

]