from django.contrib import admin
from django.urls import path, include

from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("simple_cbv_render", views.RenderHtmlView.as_view()),
    path("simple_cbv_render", views.fbv_render),
]
