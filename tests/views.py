from django.shortcuts import render
from django.views.generic import TemplateView


class RenderHtmlView(TemplateView):
    template_name = "base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Render Html View"
        context["content"] = "Hello CBV!"
        return context


def fbv_render(request):
    return render(
        request,
        "base.html",
        {"title": "FBV Render", "content": "Hello FBV!"}
    )
