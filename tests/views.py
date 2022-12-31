from django.http import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View

from cbv_inspect.decorators import djcbv_exclude
from cbv_inspect.mixins import DjCbvExcludeMixin


class RenderHtmlView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Render Html View"
        context["content"] = "Hello CBV!"
        return context


class ExcludedByMixin(DjCbvExcludeMixin, TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Render Html View"
        context["content"] = "Hello CBV!"
        return context


@method_decorator(djcbv_exclude, name="dispatch")
class ExcludedByDecorator(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Render Html View"
        context["content"] = "Hello CBV!"
        return context


def fbv_render(request):
    template_name = "base.html"
    context = {"title": "FBV Render", "content": "Hello FBV!"}

    return render(request, template_name, context)


class HelloTest(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("hello from a CBV View!")
