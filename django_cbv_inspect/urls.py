from django.urls import path

from django_cbv_inspect import views


app_name = "inspector"


urlpatterns = [
    path("", views.render_panel, name="render_panel")
]
