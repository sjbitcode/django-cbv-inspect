from inspector import InspectorMixin


class TestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if hasattr(view_func, 'view_class'):
            original_bases = view_func.view_class.__bases__
            new_bases = (InspectorMixin, *original_bases)
            view_func.view_class.__bases__ = new_bases
        return
