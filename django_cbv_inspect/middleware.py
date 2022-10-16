import logging

from django.http import HttpRequest
from django.urls import resolve
from django.urls.exceptions import Resolver404

from django_cbv_inspect.mixins import InspectorMixin

from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def is_inspector_request(request):
    """
    Determine if the request is for a DebugToolbar view.
    """
    # The primary caller of this function is in the middleware which may
    # not have resolver_match set.
    try:
        resolver_match = request.resolver_match or resolve(
            request.path, getattr(request, "urlconf", None)
        )
    except Resolver404:
        return False
    return resolver_match.namespaces and resolver_match.namespaces[-1] == "inspector"


class InspectorToolbar:
    def __init__(self, request: HttpRequest):
        self.logs = self.get_logs()
        self.request = request
        self.clear_session_logs()
        self.init_logs()

    def init_logs(self):
        match = resolve(self.request.path)

        base_classes = []
        view_cls_bases = list(match.func.view_class.__bases__)

        if InspectorMixin in view_cls_bases:
            view_cls_bases.remove(InspectorMixin)

        for cls in view_cls_bases:
            base_classes.append(
                f"{cls.__module__}.{cls.__name__}"
            )

        self.request._inspector_logs = {
            "path": self.request.path,
            "logs": {},
            "view_path": match._func_path,
            "url_name": match.view_name,
            "args": match.args,
            "kwargs": match.kwargs,
            "base_classes": base_classes,
        }
        x = 1

    def get_url_name(self):
        match = resolve(self.request.path)
        func, args, kwargs = match
        # view_info["view_func"] = get_name_from_obj(func)
        # view_info["view_args"] = args
        # view_info["view_kwargs"] = kwargs

        if getattr(match, "url_name", False):
            url_name = match.url_name
            if match.namespaces:
                url_name = ":".join([*match.namespaces, url_name])
        else:
            url_name = "<unavailable>"

        return url_name
        # view_info["view_urlname"] = url_name

    def clear_session_logs(self):
        if "inspector_logs" in self.request.session:
            del self.request.session["inspector_logs"]
        self.request.session["inspector_logs"] = {"path": self.request.path, "logs": {}}

    def get_logs(self):
        from django_cbv_inspect.mixins import INSPECT_LOGS

        if INSPECT_LOGS:
            logger.warning("logs are non-empty! clearing now...")
            INSPECT_LOGS.clear()
        return INSPECT_LOGS

    def get_content(self):
        from django_cbv_inspect import views

        return views.render_panel(self.request)


class InspectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        i = InspectorToolbar(request)

        response = self.get_response(request)

        # Is this an inspector request?
        print(request.path)

        # Check debug_toolbar/toolbar.py > is_toolbar_request method
        if is_inspector_request(request):
            return response
        # resolver_match = getattr(request, 'resolver_match', None)
        # if not resolver_match:
        #     resolver_match = resolve(request.path, getattr(request, 'urlconf', None))

        # print(f'{request.resolver_match=}')
        # if resolver_match.namespaces[-1] == 'inspector':
        #     print('YES ITS A CBV INSPECTOR REQUEST')
        #     return response

        # for log in INSPECT_LOGS:
        #     pprint(INSPECT_LOGS[log])

        if hasattr(response, "content"):
            soup = BeautifulSoup(response.content.decode(), "html.parser")
            if soup.body:
                inspector_html = i.get_content()
                soup2 = BeautifulSoup(inspector_html, "html.parser")
                # tag = soup.new_tag("h1")
                # tag.string = "TEST INSPECTOR HTML"
                last_el = soup.body.contents[-1]
                last_el.insert_after(soup2)
                response.content = str(soup)

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(view_func, "view_class"):
            # request._inspector_logs["view_path"] = f"{view_func.__module__}.{view_func.view_class.__name__}"

            if InspectorMixin not in view_func.view_class.__bases__:
                original_bases = view_func.view_class.__bases__
                new_bases = (InspectorMixin, *original_bases)
                view_func.view_class.__bases__ = new_bases
        return
