# urls.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


from django.urls import path

from . import views


app_name = "sandbox"

urlpatterns = [
    path(r'environments/<uuid:env>/', views.EnvView.as_view(), name="environment"),
    path(r'files/<uuid:env>/<path:path>', views.FileView.as_view(), name="file"),
    path(r'specifications/', views.specifications, name="specs"),
    path(r'libraries/', views.libraries, name="libraries"),
    path(r'execute/', views.execute, name="execute"),
]
