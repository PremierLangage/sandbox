# coding: utf-8


from django.urls import path
from sandbox import views

app_name = "sandbox"

urlpatterns = [
    path(r'', views.IndexView.as_view(), name="index"),
    path(r'version/', views.VersionView.as_view(), name="version"),
    path(r'env/<str:env>/', views.EnvView.as_view(), name="env"),
    path(r'build/', views.BuildView.as_view(), name="build"),
    path(r'eval/<str:env>/', views.EvalView.as_view(), name="eval"),
]
