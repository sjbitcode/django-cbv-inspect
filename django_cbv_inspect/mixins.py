import dataclasses
from dataclasses import dataclass, field
import functools
import inspect
import logging
from pprint import pformat
import re
import sys
from typing import Any, Callable

from django import get_version
from django.utils.functional import cached_property


logger = logging.getLogger(__name__)


def get_ccbv_link(attr):
    """
    attr_module: str|module
    attr: function|class
    is_method: bool

    # older versions of Django (1.4 - 1.7) have views from django.contrib.formtools.wizard, but we're skipping those.
    """

    module = attr.__module__
    from_generic = module.startswith("django.views.generic")
    from_auth = module.startswith("django.contrib.auth.views")

    if from_generic or from_auth:
        version = get_version().rsplit(".", 1)[0]

        if inspect.isroutine(attr):  # function or bound method?
            class_name, method_name = attr.__qualname__.split(".", 1)
            # https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"
        elif inspect.isclass(attr):
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{attr.__name__}"


def get_path(attr):
    """
    Returns file path of a module.
    """
    path = inspect.getfile(attr)
    sp_str = "/site-packages/"
    index = path.find(sp_str)

    # For site-packages paths, display path starting from /<package-name>/
    if index > -1:
        path = path[index + len(sp_str) - 1:]

    return path


def stringify_and_clean(object) -> str:
    formatted = pformat(object)

    clean_funcs = [coalesce_request, coalesce_queryset]

    for func in clean_funcs:
        formatted = func(formatted)

    return formatted


def coalesce_request(s: str):
    pattern = re.compile("<WSGIRequest: .*?>")
    coalesce_str = "<<request>>"
    return re.sub(pattern, coalesce_str, s)


def coalesce_queryset(s: str):
    pattern = re.compile("<QuerySet \[<(?P<modelName>\w+):.*?\]>")
    coalesce_str = "<<queryset of \g<modelName>>>"
    return re.sub(pattern, coalesce_str, s)


def get_super_calls(cls, attr: Callable) -> list:
    source = inspect.getsource(attr)
    # SUPER_PATTERN = re.compile("(super\(.*\)\.(?P<methodName>\w+)\(.+\))")
    SUPER_PATTERN = re.compile("(super\(.*\)\.(?P<methodName>\w+)(?P<methodSignature>\(.+\)))")
    matches = re.findall(SUPER_PATTERN, source)
    # base_classes = list(cls.__mro__[2:])
    base_classes = list(cls.__mro__)
    base_classes.remove(DjCBVInspectMixin)
    new_matches = []
    method_info = {}

    for match in matches:  # for each super call
        super_call = match[0]
        method = match[1]
        signature = match[2]
        # need to maybe add support for nested class? https://stackoverflow.com/a/55767059
        attr_cls = vars(sys.modules[attr.__module__])[attr.__qualname__.split('.')[0]]

        if super_call.startswith("super()"):
            for bc in base_classes[base_classes.index(attr_cls)+1:]:

                if hasattr(bc, method):
                    attr2 = getattr(bc, method)
                    if bc.__name__ in attr2.__qualname__:

                        method_info = {
                            'ccbv_link': get_ccbv_link(attr2),
                            # 'method': match[0].replace("super()", bc.__name__, 1).replace(signature, ''),
                            'method': f"{bc.__name__}.{method}",
                            'signature': str(inspect.signature(attr2))
                        }
                        # new_matches.append(method_info)
                        break
        else:
            method_info = {
                'ccbv_link': get_ccbv_link(attr),
                'method': method[0].replace(signature, ''),
                'signature': signature,
            }

        new_matches.append(method_info)

    return new_matches


@dataclass
class FunctionLog:
    tab_index: int = 0
    ordering: int = 0
    padding: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    arguments: dict = field(default_factory=dict)
    super_calls: list = field(default_factory=list)
    name: str = None
    ret_value: Any = None
    ccbv_link: str = None
    path: str = None
    signature: str = None


class DjCBVInspectMixin:
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
                print(
                    f"{tab*self.tab_index} ({self.func_order}) QUALNAME --> {attr.__qualname__}"
                )
                f.ordering = self.func_order
                f.tab_index = self.tab_index
                f.padding = f.tab_index * 30

                # Prep for next call
                self.tab_index += 1
                self.func_order += 1
                res = attr(*args, **kwargs)

                # Update function log
                f.name = attr.__qualname__
                f.args = stringify_and_clean(args)
                f.kwargs = stringify_and_clean(kwargs)
                f.ret_value = stringify_and_clean(res)

                # Get some metadata
                f.ccbv_link = get_ccbv_link(attr)
                f.path = get_path(attr)

                f.signature = inspect.formatargspec(*inspect.getfullargspec(attr))
                f.arguments = pformat(inspect.getcallargs(attr, *args, **kwargs))
                f.super_calls = get_super_calls(self.__class__, attr)
                # import pdb

                # pdb.set_trace()
                # func_signature = signature(attr)
                # bounded_args = func_signature.bind(*args, **kwargs)
                # bounded_args.apply_defaults()
                # f.signature = str(func_signature)
                # f.bound_args = str(bounded_args.arguments)

                # print(f.signature)
                # print(f.bound_args)
                # import pdb

                # pdb.set_trace()

                # Store function log
                self.request._djcbv_inspect_metadata["logs"][f.ordering] = dataclasses.asdict(f)

                self.tab_index -= 1
                print(
                    f"{tab*self.tab_index} ({f.ordering}) Result: {attr.__qualname__} call is {res}"
                )

                return res

            return wrapper
        return attr
