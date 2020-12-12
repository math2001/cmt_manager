from django.urls import path
from . import views

app_name = "enabler"
urlpatterns = [
    path("", views.index, name="index"),
    path("update-probes-conf", views.update_probes_conf, name="update-probes-conf"),
    path("conf", views.conf, name="conf"),
    path("fetch-probes-checks", views.fetch_probes_checks, name="fetch-probes-checks"),
]
