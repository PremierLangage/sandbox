from django.urls import path

from . import views

app_name = "api_server"

urlpatterns = [
   path('loader/fr/<int:id>/', views.FrozenViewSet.as_view({'get':'get'}), name='frozen_get'),
   path('loader/fr/', views.FrozenViewSet.as_view({'post':'post'}), name='frozen_post'),
   path('loader/demo/pl/', views.CallSandboxViewSet.as_view({'post':'play_demo'}), name='play_demo'),
   path('loader/play/pl/', views.CallSandboxViewSet.as_view({'post':'play_exo'}), name='play_exo'),
]