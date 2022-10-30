import logging

from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def render_djcbv_panel(request):
    djcbv_inspect_metadata = getattr(request, "_djcbv_inspect_metadata", {})
    ctx_data = {**djcbv_inspect_metadata}
    logs = ctx_data["logs"]

    if logs:
        sorted_logs = dict(sorted(logs.items()))
        ctx_data.update({"logs": sorted_logs})

    return render_to_string("django_cbv_inspect/cbv_logs2.html", ctx_data)
