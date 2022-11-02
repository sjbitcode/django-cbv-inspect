import inspect
from pprint import pformat
import re
from typing import Any, Callable, Dict, List, Type, Union, Optional

from django import get_version


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


def stringify_and_clean(object: Union[tuple | Dict | List | Any]) -> str:
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
