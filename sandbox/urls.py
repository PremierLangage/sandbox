"""
URL configuration for sandbox project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from sandbox import views

app_name = "sandbox"

urlpatterns = [
    path(r"environments/<uuid:env>/", views.EnvView.as_view(), name="environment"),
    path(r"files/<uuid:env>/<path:path>/", views.FileView.as_view(), name="file"),
    path(r"specifications/", views.SpecificationsView.as_view(), name="specs"),
    path(r"usages/", views.UsageView.as_view(), name="usage"),
    path(r"libraries/", views.LibrariesView.as_view(), name="libraries"),
    path(r"execute/", views.ExecuteView.as_view(), name="execute"),
]
