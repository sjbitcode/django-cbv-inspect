from dataclasses import dataclass
import functools
import inspect
import logging
from pprint import pformat
import re
from typing import Any, Callable, Dict, List, Type, Union, Optional

from django import get_version
from django.http import HttpRequest

from django_cbv_inspect import mixins


logger = logging.getLogger(__name__)


@dataclass
class DjCBVClassOrMethodInfo:
    ccbv_link: str = None
    name: str = None
    signature: str = None


def collect_parent_classes(view_func, cls_attr):
    """
    Iterate over view.func.cls_attr and return all classes except DjCBVInspectMixin
    """
    if hasattr(view_func, 'view_class'):
        classes = []

        for cls in getattr(view_func.view_class, cls_attr, []):
            if cls is not mixins.DjCBVInspectMixin:
                classes.append(
                    DjCBVClassOrMethodInfo(
                        ccbv_link=get_ccbv_link(cls),
                        name=f"{cls.__module__}.{cls.__name__}"
                    )
                )

        return classes


get_bases = functools.partial(collect_parent_classes, cls_attr='__bases__')
get_mro = functools.partial(collect_parent_classes, cls_attr='__mro__')


def get_ccbv_link(attr: Callable) -> Optional[str]:
    """
    note: older versions of Django (1.4 - 1.7) have views from django.contrib.formtools.wizard, but we're skipping those.
    example: https://ccbv.co.uk/projects/Django/2.0/django.views.generic.base/View/#_allowed_methods
    """

    module = attr.__module__
    from_generic = module.startswith("django.views.generic")
    from_auth = module.startswith("django.contrib.auth.views")

    if from_generic or from_auth:
        version = get_version().rsplit(".", 1)[0]

        if inspect.isroutine(attr):  # function or bound method?
            class_name, method_name = attr.__qualname__.split(".", 1)
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"
        elif inspect.isclass(attr):
            return f"https://ccbv.co.uk/projects/Django/{version}/{module}/{attr.__name__}"


def get_path(attr: Callable) -> str:
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


def serialize_params(object: Union[tuple, Dict, List, Any]) -> str:
    formatted = pformat(object)

    clean_funcs = [coalesce_request, coalesce_queryset]

    for func in clean_funcs:
        formatted = func(formatted)

    return formatted


def coalesce_request(s: str) -> str:
    pattern = re.compile("<WSGIRequest: .*?>")
    coalesce_str = "<<request>>"
    return re.sub(pattern, coalesce_str, s)


def coalesce_queryset(s: str) -> str:
    pattern = re.compile("<QuerySet \[<(?P<modelName>\w+):.*?\]>")
    coalesce_str = "<<queryset of \g<modelName>>>"
    return re.sub(pattern, coalesce_str, s)


def get_cls_from_attr(attr: Callable) -> Type:
    # reference https://stackoverflow.com/a/55767059
    return vars(inspect.getmodule(attr))[attr.__qualname__.rsplit('.', 1)[0]]


def get_sourcecode(attr: Callable) -> str:
    source = inspect.getsource(attr)

    # remove docstring if it exists
    if attr.__doc__:
        source = source.replace(attr.__doc__, '', 1)

    return re.sub(re.compile(r'#.*?\n'), '', source)


def get_super_calls(cls: Type, attr: Callable) -> List:
    source = get_sourcecode(attr)
    SUPER_PATTERN = re.compile(r"(super\(.*\)\.(?P<methodName>\w+)\(.*\))")  # this matches all including commented!!
    matches = re.findall(SUPER_PATTERN, source)
    base_classes = list(filter(lambda x: x.__name__ != "DjCBVInspectMixin", cls.__mro__))
    super_calls = []

    for match in matches:  # for each super call
        _, method_name = match
        attr_cls = get_cls_from_attr(attr)
        method_info = {}

        for bc in base_classes[base_classes.index(attr_cls)+1:]:  # remaining classes

            # check if base class has method
            if hasattr(bc, method_name):
                attr2 = getattr(bc, method_name)

                # At this point, attr2's real class can be bc or not.
                # But we don't need to iterate until we get to attr2's real parent class,
                # we can capture the info here and break
                # ex. ListView hasattr get_context_data is true, but the method is defined on MultipleObjectMixin
                # if bc is get_cls_from_attr(attr2):
                method_info = DjCBVClassOrMethodInfo(
                    ccbv_link=get_ccbv_link(attr2),
                    name=attr2.__qualname__,
                    signature=str(inspect.signature(attr2))
                )
                break
        super_calls.append(method_info)

    return super_calls


def get_request(instance: object, attr: Callable, *args: Any) -> Optional[HttpRequest]:
    if hasattr(instance, 'request'):
        return instance.request

    if attr.__name__ == 'setup':
        if isinstance(args[0], HttpRequest):
            return args[0]

    for arg in args:
        if isinstance(arg, HttpRequest):
            return arg
