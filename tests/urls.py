from django.contrib import admin
from django.urls import path

from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("simple_cbv_render", views.RenderHtmlView.as_view()),
    path("djcbv_exclude_mixin", views.ExcludedByMixin.as_view()),
    path("djcbv_exclude_dec", views.ExcludedByDecorator.as_view()),
    path("simple_fbv_render", views.fbv_render),
    path("hello_cbv", views.HelloTest.as_view()),
]
