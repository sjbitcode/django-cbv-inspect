import logging
import re
from typing import Callable, Dict, Tuple, Optional, Union

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import resolve

from django_cbv_inspect.mixins import DjCbvInspectMixin
from django_cbv_inspect import utils, views


logger = logging.getLogger(__name__)


class DjCbvToolbar:
    def __init__(self, request):
        self.request = request
        self.init_logs()

    def init_logs(self) -> None:
        match = resolve(self.request.path)

        metadata = utils.DjCbvRequestMetadata(
            path=self.request.path,
            method=self.request.method,
            view_path=match._func_path,
            url_name=match.view_name,
            args=match.args,
            kwargs=match.kwargs,
            base_classes=utils.get_bases(match.func.view_class),
            mro=utils.get_mro(match.func.view_class),
        )

        self.request._djcbv_inspect_metadata = metadata

    def get_content(self) -> None:
        return views.render_djcbv_panel(self.request)


class DjCbvInspectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def show_toolbar() -> bool:
        return settings.DEBUG

    @staticmethod
    def _is_response_insertable(response: HttpResponse) -> bool:
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

    @staticmethod
    def _remove_djcbv_mixin(request: HttpRequest) -> None:
        """
        Remove mixin if its present in cbv view function.
        """
        view_func = resolve(request.path).func

        view_func.view_class.__bases__ = tuple(
            x for x in view_func.view_class.__bases__ if x is not DjCbvInspectMixin
        )

    @staticmethod
    def _add_djcbv_mixin(view_func: Callable) -> None:
        """
        Add mixin to view function.
        """
        view_func.view_class.__bases__ = (
            DjCbvInspectMixin,
            *view_func.view_class.__bases__
        )

    @staticmethod
    def is_view_excluded(request: HttpRequest) -> bool:
        view_func = resolve(request.path).func

        if hasattr(view_func, 'djcbv_exclude'):
            return True

        return False

    def should_process_request(self, request):
        """
        Determine if the middleware should process the request.

        Will process requests meet the following criteria
            1. class-based views
            2. show_toolbar True
            3. view not excluded
        """
        if not utils.is_cbv_request(request):
            return False

        if not self.show_toolbar():
            return False

        if self.is_view_excluded(request):
            return False

        return True

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not self.should_process_request(request):
            return self.get_response(request)

        toolbar = DjCbvToolbar(request)

        response = self.get_response(request)

        self._remove_djcbv_mixin(request)

        if self._is_response_insertable(response):
            content = response.content.decode(response.charset)
            INSERT_BEFORE = "</body>"
            response_parts = re.split(INSERT_BEFORE, content, flags=re.IGNORECASE)

            # insert djCbv content before closing body tag
            if len(response_parts) > 1:
                djcbv_content = toolbar.get_content()
                response_parts[-2] += djcbv_content
                response.content = INSERT_BEFORE.join(response_parts)

                if "Content-Length" in response:
                    response["Content-Length"] = len(response.content)

        return response

    def process_view(self, request: HttpResponse, view_func: Callable, view_args: Tuple, view_kwargs: Dict) -> None:
        if self.should_process_request(request):
            self._add_djcbv_mixin(view_func)
