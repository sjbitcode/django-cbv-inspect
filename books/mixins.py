import inspect
import functools


class InspectorMixin:
    tab_index = 0

    @property
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

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                print(f"{tab*self.tab_index} QUALNAME --> {attr.__qualname__}")
                print(
                    f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                )
                # print(inspect.getsource(attr))
                # print(inspect.getframeinfo(inspect.currentframe()).function)
                self.tab_index += 1

                res = attr(*args, **kwargs)
                print(
                    f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                )

                self.tab_index -= 1
                print(f"{tab*self.tab_index} After calling {attr.__qualname__}")
                return res

            return wrapper
        return attr
