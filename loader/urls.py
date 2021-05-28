from django.urls import path

from . import views

app_name = "loader"

urlpatterns = [
   path('loader/pla/', views.FrozenViewSet.as_view({'post', 'post_pla'}), name='post_pla'),
   path('loader/pl/', views.FrozenViewSet.as_view({'get', 'post_pl'}), name='post_pl')
]