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


def get_cls_from_attr(attr):
    # reference https://stackoverflow.com/a/55767059
    attr_cls = vars(inspect.getmodule(attr))[attr.__qualname__.rsplit('.', 1)[0]]

    return attr_cls


def get_sourcecode(attr):
    source = inspect.getsource(attr)

    # remove docstring if it exists
    if attr.__doc__:
        source = source.replace(attr.__doc__, '', 1)

    return re.sub(re.compile(r'#.*?\n'), '', source)


def get_super_calls(cls, attr: Callable) -> list:
    source = get_sourcecode(attr)
    SUPER_PATTERN = re.compile(r"(super\(.*\)\.(?P<methodName>\w+)(?P<methodSignature>\(.*\)))")  # this matches all including commented!!
    matches = re.findall(SUPER_PATTERN, source)
    base_classes = list(filter(lambda x: x.__name__ != "DjCBVInspectMixin", cls.__mro__))
    new_matches = []
    method_info = {}

    for match in matches:  # for each super call
        super_call, method_name, arguments = match
        attr_cls = get_cls_from_attr(attr)

        for bc in base_classes[base_classes.index(attr_cls)+1:]:  # remaining classes

            if hasattr(bc, method_name):
                attr2 = getattr(bc, method_name)

                if bc is get_cls_from_attr(attr2):

                    method_info = {
                        'ccbv_link': get_ccbv_link(attr2),
                        'method': attr2.__qualname__,
                        'signature': str(inspect.signature(attr2))
                    }
                    break
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
    is_parent: bool = False
    parent_list: list = field(default_factory=list)
    name: str = None
    ret_value: Any = None
    ccbv_link: str = None
    path: str = None
    signature: str = None

    @property
    def parents(self):
        return " ".join(self.parent_list)


class DjCBVInspectMixin:
    tab_index = 0
    func_order = 1
    DJCBV_LOGS = {}

    @cached_property
    def allowed_callables(self):
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
            and name in self.allowed_callables
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
                self.DJCBV_LOGS[f.ordering] = f

                # The following try/except sets parents and parent statuses on the current and prior log, respectively.
                try:
                    prior_log = self.DJCBV_LOGS[f.ordering-1]

                    # is prior log a parent of current log?
                    if prior_log.tab_index < f.tab_index:
                        prior_log.is_parent = True
                        f.parent_list.append(f"cbvInspect_{prior_log.ordering}_{prior_log.tab_index}")

                        # copy the parent's parents and assign to current log
                        if prior_log.parent_list:
                            f.parent_list = prior_log.parent_list + f.parent_list

                    # if prior log not a parent, then check previous logs to find any parents
                    else:
                        # get logs keys up to the current log
                        ancestor_log_keys = list(range(1, f.ordering))

                        # iterate over list backwards to get the closest parent faster
                        for key in ancestor_log_keys[::-1]:
                            ancestor_log = self.DJCBV_LOGS[key]

                            # if ancestor log is current log's legitimate ancestor, take its parents and stop iteration
                            if ancestor_log.is_parent and ancestor_log.tab_index < f.tab_index:
                                f.parent_list = ancestor_log.parent_list + [f"cbvInspect_{ancestor_log.ordering}_{ancestor_log.tab_index}"]
                                break
                except KeyError:
                    pass

                # Prep for next call
                self.tab_index += 1
                self.func_order += 1

                res = attr(*args, **kwargs)

                f.ret_value = stringify_and_clean(res)
                f.name = attr.__qualname__
                f.args = stringify_and_clean(args)
                f.kwargs = stringify_and_clean(kwargs)
                f.signature = inspect.formatargspec(*inspect.getfullargspec(attr))
                f.ccbv_link = get_ccbv_link(attr)
                f.path = get_path(attr)
                f.super_calls = get_super_calls(self.__class__, attr)

                # update entry
                self.request._djcbv_inspect_metadata["logs"][f.ordering] = f

                self.tab_index -= 1
                print(
                    f"{tab*self.tab_index} ({f.ordering}) Result: {attr.__qualname__} call is {res}"
                )

                return res

            return wrapper
        return attr
