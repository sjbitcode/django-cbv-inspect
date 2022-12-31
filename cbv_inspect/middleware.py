import re
from typing import Callable, Dict, Tuple

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import ResolverMatch, resolve

from cbv_inspect import utils, views
from cbv_inspect.mixins import DjCbvInspectMixin


class DjCbvToolbar:
    def __init__(self, request: HttpRequest) -> None:
        self.request = request
        self.init_logs()

    def init_logs(self) -> None:
        """
        Attach metadata to request object.
        """

        match: ResolverMatch = resolve(self.request.path)

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

    def get_content(self) -> str:
        """
        Render the djCbv toolbar and return stringified markup.
        """
        return views.render_djcbv_panel(self.request)


class DjCbvInspectMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    @staticmethod
    def show_toolbar() -> bool:
        return settings.DEBUG

    @staticmethod
    def _is_response_insertable(response: HttpResponse) -> bool:
        """
        Determine if djCbv content can be inserted into a response.
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
        Remove mixin if its present in a request's CBV view class.
        """

        view_func = resolve(request.path).func

        view_func.view_class.__bases__ = tuple(
            x for x in view_func.view_class.__bases__ if x is not DjCbvInspectMixin
        )

    @staticmethod
    def _add_djcbv_mixin(view_func: Callable) -> None:
        """
        Insert mixin in a CBV view class.
        """

        view_func.view_class.__bases__ = (
            DjCbvInspectMixin,
            *view_func.view_class.__bases__
        )

    @staticmethod
    def is_view_excluded(request: HttpRequest) -> bool:
        """
        Check for `djcbv_exclude` attribute on view function.
        """

        view_func = resolve(request.path).func

        if hasattr(view_func, 'djcbv_exclude'):
            return True

        return False

    def should_process_request(self, request: HttpRequest) -> bool:
        """
        Determine if the middleware should process the request.

        Will process requests that meet the following criteria:
            1. class-based views
            2. show_toolbar is True
            3. view is not excluded
        """

        if not utils.is_cbv_request(request):
            return False

        if not self.show_toolbar():
            return False

        if self.is_view_excluded(request):
            return False

        return True

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        This is the entrypoint of django-cbv-inspect.

        For incoming requests:
            1. check if request should be processed
            2. prep the request object by attaching metadata object to it
            3. attach the mixin to cbv class before view gets called

        For outgoing responses:
            1. remove the mixin from cbv class
            2. render the djCbv toolbar html and attach to response
        """

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
