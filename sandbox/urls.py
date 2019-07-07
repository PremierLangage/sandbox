# urls.py
#
# Authors:
#   - Coumes Quentin <coumes.quentin@gmail.com>


from django.urls import path

from sandbox import views


app_name = "sandbox"

urlpatterns = [
    path(r'environments/<uuid:env>/', views.EnvView.as_view(), name="environment"),
    path(r'files/<uuid:env>/<path:path>', views.FileView.as_view(), name="file"),
    path(r'files/<uuid:env>/', views.list_file, name="list_file"),
    path(r'specifications/', views.specifications, name="specifications"),
    path(r'libraries/', views.libraries, name="libraries"),
    path(r'execute/', views.execute, name="execute"),
]
