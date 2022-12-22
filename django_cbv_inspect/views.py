from dataclasses import fields
import logging

from django.utils.safestring import SafeString
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def render_djcbv_panel(request) -> SafeString:
    metadata = getattr(request, "_djcbv_inspect_metadata")

    # creates a shallow copy because we want to keep each logs as a dataclass object
    ctx_data = dict((field.name, getattr(metadata, field.name)) for field in fields(metadata))

    return render_to_string("django_cbv_inspect/cbv_logs2.html", ctx_data)
