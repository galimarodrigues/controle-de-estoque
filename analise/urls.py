from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.dashboard_analise,
        name="dashboard_analise",
    ),
]