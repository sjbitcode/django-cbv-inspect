from __future__ import annotations

from dataclasses import dataclass
import functools
import inspect
import logging
from pprint import pformat
import re
from typing import Any, Callable, Dict, List, Literal, Type, Union, Optional

from django import get_version
from django.http import HttpRequest

from django_cbv_inspect import mixins


logger = logging.getLogger(__name__)


@dataclass
class DjCBVClassOrMethodInfo:
    ccbv_link: str = None
    name: str = None
    signature: str = None


def is_view_cbv(func: Callable) -> bool:
    """
    Determine if a function is a result of a CBV as_view() call.
    """
    return hasattr(func, "view_class")


def collect_parent_classes(cls: Type, attr: Literal["__mro__", "__bases__"]):
    """
    Iterate over cls.attr and return all classes except DjCBVInspectMixin
    """
    classes = []

    for cls in getattr(cls, attr, []):
        if cls is not mixins.DjCBVInspectMixin:
            classes.append(
                DjCBVClassOrMethodInfo(
                    ccbv_link=get_ccbv_link(cls),
                    name=f"{cls.__module__}.{cls.__name__}"
                )
            )

    return classes


get_bases = functools.partial(collect_parent_classes, attr='__bases__')
get_mro = functools.partial(collect_parent_classes, attr='__mro__')


def get_ccbv_link(obj: Union[Callable, Type]) -> Optional[str]:
    """
    Construct the ccbv.co.uk link for a class or method.
    ex: https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods

    Note: older versions of Django (1.4 - 1.7) have views from django.contrib.formtools.wizard, but we're skipping those.
    """
    module: str = obj.__module__
    from_generic: bool = module.startswith("django.views.generic")
    from_auth: bool = module.startswith("django.contrib.auth.views")

    if from_generic or from_auth:
        version = get_version().rsplit(".", 1)[0]

        if inspect.isroutine(obj):  # function or bound method?
            class_name, method_name = obj.__qualname__.rsplit(".", 1)
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"
        elif inspect.isclass(obj):
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{obj.__name__}"


def get_path(obj: Callable) -> str:
    """
    Returns file path of a module.
    """
    path: str = inspect.getfile(obj)
    site_pkg_dir = "/site-packages/"
    index: int = path.find(site_pkg_dir)

    # For site-packages paths, display path starting from /<package-name>/
    if index > -1:
        path = path[index + len(site_pkg_dir) - 1:]

    return path


def serialize_params(obj: Any) -> str:
    """
    Return a stringified and masked representation of an object.

    This is used on arguments, keyword arguments, and return values.
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
    # pattern = re.compile("<QuerySet \[<(?P<modelName>\w+):.*?\]>")
    # mask = "<<queryset of \g<modelName>>>"
    pattern = re.compile("<QuerySet \[.*?\]>")
    mask = "<<queryset>>"
    return re.sub(pattern, mask, s)


def get_class_from_method(obj: Callable) -> Type:
    """
    Return class from module object.
    """
    # reference https://stackoverflow.com/a/55767059
    return vars(inspect.getmodule(obj))[obj.__qualname__.rsplit('.', 1)[0]]


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
        source = source.replace(obj.__doc__, '', 1)

    return re.sub(re.compile(r'#.*?\n'), '', source)


def get_super_calls(cls: Type, method: Callable) -> List:
    """
    Extract super calls from a method and for each,
    return metadata about class that the super builtin resolves and calls.
    """
    source: str = get_sourcecode(method)
    # this regex pattern includes comments, so we exclude comments above
    SUPER_PATTERN = re.compile(r"(super\(.*\)\.(?P<methodName>\w+)\(.*\))")
    matches: List = re.findall(SUPER_PATTERN, source)

    if not matches:
        return

    super_metadata: List[DjCBVClassOrMethodInfo] = []
    mro_classes: List = list(filter(lambda x: x.__name__ != "DjCBVInspectMixin", cls.__mro__))
    method_cls: Type = get_class_from_method(method)  # the class that defines this method containing super calls

    for match in matches:  # for each super call in method
        _, method_name = match
        method_info = {}

        # search remaining mro classes, after method_cls
        for mro_cls in mro_classes[mro_classes.index(method_cls)+1:]:
            if class_has_method(mro_cls, method_name):
                attr: Callable = getattr(mro_cls, method_name)

                # At this point, attr's parent class can be mro_cls or not.
                # ex:
                #   mro_cls = ListView, method_name = "get_context_data"
                #   hasattr(ListView, "get_context_data") is True, but
                #   getattr(ListView, "get_context_data") is <function MultipleObjectMixin.get_context_data ...>
                #   because the method is defined or overriden on MultipleObjectMixin.
                # We can collect this metadata without iterating further through MRO classes
                method_info = DjCBVClassOrMethodInfo(
                    ccbv_link=get_ccbv_link(attr),
                    name=attr.__qualname__,
                    signature=str(inspect.signature(attr))
                )
                break
        super_metadata.append(method_info)

    return super_metadata


def get_request(instance: object, attr: Callable, *args: Any) -> Optional[HttpRequest]:
    """
    Attempt to return an HttpRequest object from an attribute or arguments.

    The main reason is because View.setup is the first CBV method that runs
    and sets the request object on the CBV instance.
    The DjCBVInspectMixin needs access to the request object before View.setup
    runs so it attempts to grab it from aruments.
    """
    if hasattr(instance, 'request'):
        return instance.request

    if attr.__name__ == 'setup':
        if isinstance(args[0], HttpRequest):
            return args[0]

    for arg in args:
        if isinstance(arg, HttpRequest):
            return arg
