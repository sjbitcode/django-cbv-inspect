from dataclasses import fields

from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from cbv_inspect.utils import DjCbvRequestMetadata


def render_djcbv_panel(request) -> SafeString:
    metadata: DjCbvRequestMetadata = getattr(request, "_djcbv_inspect_metadata")

    # creates a shallow copy of the metadata object
    # because we want to keep each log as a dataclass object
    ctx_data = dict((field.name, getattr(metadata, field.name)) for field in fields(metadata))

    return render_to_string("cbv_inspect/toolbar.html", ctx_data)
