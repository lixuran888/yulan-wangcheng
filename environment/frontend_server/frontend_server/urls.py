from django.contrib import admin
from django.urls import path

from translator import network_views


urlpatterns = [
    path("", network_views.network_simulator, name="network_simulator"),
    path("api/simulation/state/", network_views.simulation_state, name="simulation_state"),
    path("api/simulation/reset/", network_views.reset_simulation, name="reset_simulation"),
    path("api/simulation/step/", network_views.step_simulation, name="step_simulation"),
    path("api/simulation/intervention/", network_views.apply_intervention, name="apply_intervention"),
    path("admin/", admin.site.urls),
]
