import logging
import re

from django.urls import resolve

from django_cbv_inspect.mixins import DjCBVInspectMixin, get_ccbv_link


logger = logging.getLogger(__name__)


class InspectorToolbar:
    def __init__(self, request):
        self.request = request
        self.init_logs()

    def get_view_base_classes(self, view_func):
        if hasattr(view_func, 'view_class'):
            base_classes = []
            view_cls_bases = list(view_func.view_class.__bases__)

            if DjCBVInspectMixin in view_cls_bases:
                view_cls_bases.remove(DjCBVInspectMixin)

            for cls in view_cls_bases:
                cls_info = {
                    'ccbv_link': get_ccbv_link(cls),
                    'name': f"{cls.__module__}.{cls.__name__}"
                }
                base_classes.append(cls_info)

            return base_classes

    def get_mro(self, view_func):
        if hasattr(view_func, 'view_class'):
            mro = []

            for cls in view_func.view_class.__mro__:
                if cls is not DjCBVInspectMixin:
                    cls_info = {
                        'ccbv_link': get_ccbv_link(cls),
                        'name': f"{cls.__module__}.{cls.__name__}"
                    }
                    mro.append(cls_info)

            return mro

    def init_logs(self):
        match = resolve(self.request.path)

        self.request._djcbv_inspect_metadata = {
            "path": self.request.path,
            "method": self.request.method,
            "logs": {},
            "view_path": match._func_path,
            "url_name": match.view_name,
            "args": match.args,
            "kwargs": match.kwargs,
            "base_classes": self.get_view_base_classes(match.func),
            "mro": self.get_mro(match.func),
        }

    def get_content(self):
        from django_cbv_inspect import views

        return views.render_djcbv_panel(self.request)


class DjCBVInspectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _is_response_insertable(response):
        """
        Determine if djcbv_inspect content can be inserted into a response.
        """
        content_type = response.get("Content-Type", "").split(";")[0]
        content_encoding = response.get("Content-Encoding", "")

        has_content = hasattr(response, "content")
        is_html_content_type = content_type == "text/html"
        gzipped_encoded = "gzip" in content_encoding
        streaming_response = response.streaming

        return (
            has_content
            and is_html_content_type
            and not gzipped_encoded
            and not streaming_response
        )

    def __call__(self, request):
        i = InspectorToolbar(request)

        response = self.get_response(request)

        if self._is_response_insertable(response):
            content = response.content.decode(response.charset)
            INSERT_BEFORE = "</body>"
            response_parts = re.split(INSERT_BEFORE, content, flags=re.IGNORECASE)

            # insert djcbv content before closing body tag
            if len(response_parts) > 1:
                djcbv_content = i.get_content()
                response_parts[-2] += djcbv_content
                response.content = INSERT_BEFORE.join(response_parts)

                if "Content-Length" in response:
                    response["Content-Length"] = len(response.content)

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # insert djcbv mixin if class-based view
        if hasattr(view_func, "view_class"):
            if DjCBVInspectMixin not in view_func.view_class.__bases__:
                view_func.view_class.__bases__ = (
                    DjCBVInspectMixin,
                    *view_func.view_class.__bases__
                )
        return
