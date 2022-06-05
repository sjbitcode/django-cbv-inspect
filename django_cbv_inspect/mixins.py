import dataclasses
from dataclasses import dataclass, field
import functools
import inspect
import logging
from statistics import mode
from typing import Any

from django import get_version
from django.utils.functional import cached_property


logger = logging.getLogger(__name__)
INSPECT_LOGS = {}


def get_ccbv_link(attr_module, attr_func):
    module: str = attr_module.__name__
    from_generic = module.startswith('django.views.generic')
    from_auth = module.startswith('django.contrib.auth.views')

    if from_generic or from_auth:
        version = get_version().rsplit('.', 1)[0]
        class_name, method_name = attr_func.__qualname__.split('.', 1)
        # https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods
        ccbv_link = f'https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}'
        return ccbv_link

def get_path(attr_module):
    path = attr_module.__file__
    sp_str = '/site-packages/'
    index = path.find(sp_str)

    # For site-packages paths, display path starting from /<package-name>/
    if index > -1:
        path = path[(index-1)+len(sp_str):]

    return path

@dataclass
class FunctionLog:
    tab_index: int = 0
    ordering: int = 0
    padding: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    children: dict = field(default_factory=dict)
    name: str = None
    ret_value: Any = None
    ccbv_link: str = None
    path: str = None


class InspectorMixin:
    tab_index = 0
    func_order = 1

    @cached_property
    def get_whitelisted_callables(self):
        cbv_funcs = list(
            filter(
                lambda x: not x[0].startswith("__"),
                inspect.getmembers(self.__class__, inspect.isfunction),
            )
        )
        return [func[0] for func in cbv_funcs]

    def __getattribute__(self, name: str):
        attr = super().__getattribute__(name)

        if (
            callable(attr)
            and name != "__class__"
            and attr.__name__ in self.get_whitelisted_callables
        ):
            tab = "\t"
            f = FunctionLog()

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                f.ordering = self.func_order
                print(f"{tab*self.tab_index} ({self.func_order}) QUALNAME --> {attr.__qualname__}")

                # Prep for next call
                self.tab_index += 1
                self.func_order += 1
                res = attr(*args, **kwargs)

                # Update function log
                f.name = attr.__qualname__
                f.args = str(args)
                f.kwargs = str(kwargs)
                f.ret_value = str(res)
                # Get some metadata
                module = inspect.getmodule(attr)
                f.ccbv_link = get_ccbv_link(module, attr)
                f.path = get_path(module)
                f.tab_index = self.tab_index
                f.padding = f.tab_index * 30

                # Store function log
                self.request._inspector_logs['logs'][f.ordering] = dataclasses.asdict(f)
                global INSPECT_LOGS
                INSPECT_LOGS[f.ordering] = f
    
                self.tab_index -= 1
                print(f"{tab*self.tab_index} ({f.ordering}) Result: {attr.__qualname__} call is {res}")

                return res

            return wrapper
        return attr