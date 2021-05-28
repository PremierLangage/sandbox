from typing import FrozenSet
from django.urls import path

from . import views

app_name = "loader"

urlpatterns = [
   path('loader/pla/', views.FrozenViewSet.as_view({'post': 'post_frozen'}), name='post_frozen'),
   path('loader/fr/', views.FrozenViewSet.as_list(), name='frozen-list'),
   path('loader/fr/<str:hash>/', views.FrozenViewSet.as_detail(), name='frozen-detail'),
]