from dataclasses import dataclass, field
import functools
import inspect
from typing import Any

from django import get_version
from django.utils.functional import cached_property


INSPECT_LOGS = {}


def get_ccbv_link(attr_name):
    module = inspect.getmodule(attr_name).__name__
    from_generic = module.startswith('django.views.generic')
    from_auth = module.startswith('django.contrib.auth.views')

    if from_generic or from_auth:
        version = get_version().rsplit('.', 1)[0]
        class_name, method_name = attr_name.__qualname__.split('.', 1)
        # https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods
        ccbv_link = f'https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}'
        return ccbv_link

@dataclass
class FunctionLog:
    tab_index: int = 0
    ordering: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    name: str = None
    ret_value: Any = None
    ccbv_link: str = None


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
                # print(inspect.getsource(attr))
                # self.tab_index += 1
                # self.func_order += 1
                f.ordering = self.func_order

                print(f"{tab*self.tab_index} ({self.func_order}) QUALNAME --> {attr.__qualname__}")
                # print(
                #     f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                # )
                # print(f"{tab*self.tab_index} FUNC ORDER --> ", self.func_order)
                self.tab_index += 1
                self.func_order += 1
                res = attr(*args, **kwargs)
                # print(
                #     f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                # )

                # Update function log
                f.name = attr.__qualname__
                f.args = args
                f.kwargs = kwargs
                f.ret_value = res
                f.ccbv_link = get_ccbv_link(attr)

                global INSPECT_LOGS
                INSPECT_LOGS[f.ordering] = f

                self.tab_index -= 1
                f.tab_index = self.tab_index
                print(
                    f"{tab*self.tab_index} ({f.ordering}) Result: {attr.__qualname__} call is {res}"
                )
                # print(f"{tab*self.tab_index} After calling {attr.__qualname__}\n")
                return res

            return wrapper
        return attr