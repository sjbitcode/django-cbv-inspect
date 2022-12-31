from __future__ import annotations

import functools
import inspect
import re
from dataclasses import dataclass, field
from pprint import pformat
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Type, Union

from django import get_version
from django.http import HttpRequest
from django.urls import resolve

from cbv_inspect import mixins


class DjCbvException(Exception):
    pass


@dataclass
class DjCbvRequestMetadata:
    """
    Dataclass to store djCbv request metadata.

    This is attached to the HttpRequest object like `request._djcbv_inspect_metadata`.
    """

    path: str
    method: str
    view_path: str
    url_name: str
    args: Tuple[Any]
    kwargs: Dict[str, Any]
    logs: Dict = field(default_factory=dict)
    base_classes: Optional[List] = None
    mro: Optional[List] = None


@dataclass
class DjCbvLog:
    """
    Dataclass to store logs for a class-based view execution.

    Log instances are stored on the `request._djcbv_inspect_metadata.logs` list.
    """

    order: int = 0
    indent: int = 0

    is_parent: bool = False
    parent_list: List[str] = field(default_factory=list)

    name: str = None
    args: Tuple[str] = field(default_factory=tuple)
    kwargs: Dict[str, str] = field(default_factory=dict)
    return_value: Any = None
    signature: str = None
    path: str = None
    super_calls: List[str] = field(default_factory=list)
    ccbv_link: str = None

    @property
    def parents(self) -> str:
        return " ".join(self.parent_list)

    @property
    def padding(self) -> int:
        return self.indent * 30


@dataclass
class DjCbvClassOrMethodInfo:
    """
    Dataclass to store common metadata about a method or class.
    """

    ccbv_link: str = None
    name: str = None
    signature: str = None


def is_cbv_view(func: Callable) -> bool:
    """
    Determine if a function is a result of a CBV as_view() call.
    """
    return hasattr(func, "view_class")


def is_cbv_request(request: HttpRequest) -> bool:
    """
    Determine if a request will map to a CBV.
    """

    view_func = resolve(request.path).func

    return is_cbv_view(view_func)


def collect_parent_classes(cls: Type, attr: Literal["__mro__", "__bases__"]) -> List:
    """
    Return metadata for all mro or base classes except for DjCBVInspectMixin.
    """

    classes = []

    for cls in getattr(cls, attr, []):
        if cls is not mixins.DjCbvInspectMixin:
            classes.append(
                DjCbvClassOrMethodInfo(
                    ccbv_link=get_ccbv_link(cls), name=f"{cls.__module__}.{cls.__name__}"
                )
            )

    return classes


get_bases = functools.partial(collect_parent_classes, attr="__bases__")
get_mro = functools.partial(collect_parent_classes, attr="__mro__")


def get_ccbv_link(obj: Union[Callable, Type]) -> Optional[str]:
    """
    Construct the ccbv.co.uk link for a class or method.
    ex: https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods

    Note: older versions of Django (1.4 - 1.7) have views from django.contrib.formtools.wizard,
    but we're skipping those.
    """

    module: str = obj.__module__
    from_generic: bool = module.startswith("django.views.generic")
    from_auth: bool = module.startswith("django.contrib.auth.views")

    if from_generic or from_auth:
        version = get_version().rsplit(".", 1)[0]

        if inspect.isroutine(obj):  # function or bound method?
            class_name, method_name = obj.__qualname__.rsplit(".", 1)
            return (
                f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"
            )

        if inspect.isclass(obj):
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{obj.__name__}"


def get_path(obj: Callable) -> str:
    """
    Return file path of a module.

    Note: site packages path start from package name.
    """

    path: str = inspect.getfile(obj)
    site_pkg_dir = "/site-packages/"
    index: int = path.find(site_pkg_dir)

    # For site-packages paths, display path starting from /<package-name>/
    if index > -1:
        path = path[index + len(site_pkg_dir) - 1 :]

    return path


def serialize_params(obj: Any) -> str:
    """
    Return a stringified and masked representation of an object for
    function arguments, keyword arguments, and return values.
    """

    formatted: str = pformat(obj)

    clean_funcs = [mask_request, mask_queryset]

    for clean_func in clean_funcs:
        formatted = clean_func(formatted)

    return formatted


def mask_request(s: str) -> str:
    """
    Subsitute an HttpRequests's string representation with a masked value.
    """

    pattern = re.compile("<WSGIRequest: .*?>")
    mask = "<<request>>"
    return re.sub(pattern, mask, s)


def mask_queryset(s: str) -> str:
    """
    Substitute a QuerySet's string representation with a masked value.
    """

    pattern = re.compile(r"<QuerySet \[.*?\]>")
    mask = "<<queryset>>"
    return re.sub(pattern, mask, s)


def get_callable_source(obj: Callable) -> Type:
    """
    Return the object that defines the callable.

    Ex:
        - Given a method, this would return the class that defines it
          (not necessarily instance class)
        - Given a function, this would return the function itself
    """
    # reference https://stackoverflow.com/a/55767059
    return vars(inspect.getmodule(obj))[obj.__qualname__.rsplit(".", 1)[0]]


def class_has_method(cls: Type, method: str) -> bool:
    """
    Check if a class defines a method.
    """

    attr = getattr(cls, method, None)

    if attr:
        return callable(attr)

    return False


def get_sourcecode(obj: Callable) -> str:
    """
    Return an object's sourcecode without docstring and comments.
    """

    source: str = inspect.getsource(obj)

    # remove docstring if it exists
    if obj.__doc__:
        source = source.replace(obj.__doc__, "", 1)

    return re.sub(re.compile(r"#.*?\n"), "", source)


def get_super_calls(method: Callable) -> List:
    """
    Extract, resolve, and return metadata for all super calls defined in a bound method.
    """

    source: str = get_sourcecode(method)
    SUPER_PATTERN = re.compile(r"(super\(.*\)\.(?P<methodName>\w+)\(.*\))")
    matches: List = re.findall(SUPER_PATTERN, source)

    if not matches:
        return

    super_metadata: List[DjCbvClassOrMethodInfo] = []
    view_instance_cls = method.__self__.__class__
    mro_classes: List = list(
        filter(lambda x: x.__name__ != "DjCBVInspectMixin", view_instance_cls.__mro__)
    )
    method_cls: Type = get_callable_source(
        method
    )  # the class that defines this method containing super calls

    # for each super call in method
    for match in matches:
        _, method_name = match
        method_info = {}

        # search remaining mro classes, after method_cls
        for mro_cls in mro_classes[mro_classes.index(method_cls) + 1 :]:
            if class_has_method(mro_cls, method_name):
                attr: Callable = getattr(mro_cls, method_name)

                # At this point, attr's class can be the current mro_cls or not.
                # ex:
                #   mro_cls = ListView, method_name = "get_context_data"
                #   hasattr(ListView, "get_context_data") is True, but
                #   getattr(ListView, "get_context_data") is
                #   <function MultipleObjectMixin.get_context_data ...>
                #   because the method is defined or overriden on MultipleObjectMixin.
                # We can return this metadata without iterating further through mro classes
                method_info = DjCbvClassOrMethodInfo(
                    ccbv_link=get_ccbv_link(attr),
                    name=attr.__qualname__,
                    signature=str(inspect.signature(attr)),
                )
                break
        super_metadata.append(method_info)

    return super_metadata


def get_request(instance: object, attr: Callable, *args: Any) -> Optional[HttpRequest]:
    """
    Attempt to get an HttpRequest object from one of two places:
        1. a view class instance
        2. a view class bound method

    The main reason is because View.setup is the first CBV method that runs and
    sets the request object on the CBV instance, so we can't check `self.request`
    during the setup method!

    The DjCBVInspectMixin needs access to the request object before View.setup
    runs so it attempts to grab it from arguments. All following view methods will
    have the request available on the view class instance.
    """

    if hasattr(instance, "request"):
        return instance.request

    if attr.__name__ == "setup":
        if isinstance(args[0], HttpRequest):
            return args[0]

    raise DjCbvException("Request object could not be found!")


def set_log_parents(order: int, request: HttpRequest) -> None:
    """
    Determine if current log has parents and if so, mark prior log as a parent.

    Logs are stored in a dict accessible via `request._djcbv_inspect_metadata.logs`.

    There are two attributes on each log to help determine parent status and parent logs:
        1. `is_parent` (bool)
        2. `parent_list` (list[str])

    The parent log notation stored in `parent_list` is denoted by a string in the format
    "cbvInspect_[order]_[indent]".
    """

    try:
        current_log = request._djcbv_inspect_metadata.logs[order]
        prior_log = request._djcbv_inspect_metadata.logs[order - 1]

        # is prior log a parent of current log?
        if prior_log.indent < current_log.indent:
            prior_log.is_parent = True
            current_log.parent_list.append(f"cbvInspect_{prior_log.order}_{prior_log.indent}")

            # copy the new parent's parents and assign to current log
            if prior_log.parent_list:
                current_log.parent_list = prior_log.parent_list + current_log.parent_list

        # if prior log is not a parent, then check previous logs to find any parents
        else:
            # get log dict keys up to the current log
            ancestor_log_keys = list(range(1, current_log.order))

            # iterate over list backwards to access the closest log to get the correct parent
            for key in ancestor_log_keys[::-1]:
                ancestor_log = request._djcbv_inspect_metadata.logs[key]

                # if ancestor_log is a parent, copy its parents
                # plus itself and stop iteration
                if ancestor_log.is_parent and ancestor_log.indent < current_log.indent:
                    current_log.parent_list = ancestor_log.parent_list + [
                        f"cbvInspect_{ancestor_log.order}_{ancestor_log.indent}"
                    ]
                    break
    except KeyError:
        pass
