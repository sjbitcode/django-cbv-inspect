from dataclasses import dataclass, field
import functools
import inspect
from typing import Any

from django.utils.functional import cached_property


INSPECT_LOGS = {}

@dataclass
class FunctionLog:
    tab_index: int = 0
    ordering: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    name: str = None
    ret_value: Any = None


class InspectorMixin:
    tab_index = 0
    func_order = 0

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
                print(f"{tab*self.tab_index} QUALNAME --> {attr.__qualname__}")
                print(
                    f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                )
                print(f"{tab*self.tab_index} FUNC ORDER --> ", self.func_order)
                # print(inspect.getsource(attr))
                # print(inspect.getframeinfo(inspect.currentframe()).function)
                self.tab_index += 1
                self.func_order += 1
                f.ordering = self.func_order

                res = attr(*args, **kwargs)
                # print(
                #     f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                # )

                # Update function log
                f.name = attr.__qualname__
                f.tab_index = self.tab_index
                f.args = args
                f.kwargs = kwargs
                f.ret_value = res

                global INSPECT_LOGS
                INSPECT_LOGS[f.ordering] = f

                self.tab_index -= 1
                print(
                    f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                )
                print(f"{tab*self.tab_index} After calling {attr.__qualname__}\n")
                return res

            return wrapper
        return attr