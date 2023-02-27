from django.urls import path
from . import views

app_name = "sandbox_api"

urlpatterns = [
    path('runner/', views.RunnerView.as_view(), name="runner"),
]