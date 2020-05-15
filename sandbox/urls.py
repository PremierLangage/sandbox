# urls.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


from django.urls import path

from . import views


app_name = "sandbox"

urlpatterns = [
    path(r'environments/<uuid:env>/', views.EnvView.as_view(), name="environment"),
    path(r'files/<uuid:env>/<path:path>/', views.FileView.as_view(), name="file"),
    path(r'specifications/', views.SpecificationsView.as_view(), name="specs"),
    path(r'usages/', views.UsageView.as_view(), name="usage"),
    path(r'libraries/', views.LibrariesView.as_view(), name="libraries"),
    path(r'execute/', views.ExecuteView.as_view(), name="execute"),
]
