from django.urls import path

from . import views

app_name = "api_server"

urlpatterns = [
   path('loader/fr/', views.FrozenViewSet.as_view({'get':'get'}), name='frozen_get'),
   path('loader/fr/<str:hash>/', views.FrozenViewSet.as_view({'post':'post'}), name='frozen_post'),
   path('loader/demo/pl/', views.FrozenViewSet.as_view({'post':'play_demo'}), name='play_demo')
]
