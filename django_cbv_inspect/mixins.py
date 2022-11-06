from dataclasses import dataclass, field
import functools
import inspect
import logging
from typing import Any, Dict, List, Tuple

from django.utils.functional import cached_property

from django_cbv_inspect import utils


logger = logging.getLogger(__name__)


@dataclass
class FunctionLog:
    order: int = 0
    indent: int = 0

    is_parent: bool = False
    parent_list: List[str] = field(default_factory=list)

    return_value: Any = None
    name: str = None
    args: Tuple[str] = field(default_factory=tuple)
    kwargs: Dict[str, str] = field(default_factory=dict)
    signature: str = None
    ccbv_link: str = None
    path: str = None
    super_calls: List[str] = field(default_factory=list)

    @property
    def parents(self):
        return " ".join(self.parent_list)

    @property
    def padding(self):
        return self.indent * 30


class DjCBVInspectMixin:
    indent = 0
    order = 1

    @cached_property
    def allowed_callables(self) -> List:
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
                    f"{tab*self.indent} ({self.order}) QUALNAME --> {attr.__qualname__}"
                )
                f.order = self.order
                f.indent = self.indent

                request = utils.get_request(self, attr, *args)
                request._djcbv_inspect_metadata["logs"][f.order] = f

                # The following try/except sets parents and parent statuses on the current and prior log, respectively.
                try:
                    prior_log = request._djcbv_inspect_metadata["logs"][f.order-1]

                    # is prior log a parent of current log?
                    if prior_log.indent < f.indent:
                        prior_log.is_parent = True
                        f.parent_list.append(f"cbvInspect_{prior_log.order}_{prior_log.indent}")

                        # copy the parent's parents and assign to current log
                        if prior_log.parent_list:
                            f.parent_list = prior_log.parent_list + f.parent_list

                    # if prior log not a parent, then check previous logs to find any parents
                    else:
                        # get logs keys up to the current log
                        ancestor_log_keys = list(range(1, f.order))

                        # iterate over list backwards to get the closest parent faster
                        for key in ancestor_log_keys[::-1]:
                            ancestor_log = request._djcbv_inspect_metadata["logs"][key]

                            # if ancestor log is current log's legitimate ancestor, take its parents and stop iteration
                            if ancestor_log.is_parent and ancestor_log.indent < f.indent:
                                f.parent_list = ancestor_log.parent_list + [f"cbvInspect_{ancestor_log.order}_{ancestor_log.indent}"]
                                break
                except KeyError:
                    pass

                # Prep for next call
                self.indent += 1
                self.order += 1

                res = attr(*args, **kwargs)

                f.return_value = utils.serialize_params(res)
                f.name = attr.__qualname__
                f.args = utils.serialize_params(args)
                f.kwargs = utils.serialize_params(kwargs)
                f.signature = inspect.formatargspec(*inspect.getfullargspec(attr))
                f.ccbv_link = utils.get_ccbv_link(attr)
                f.path = utils.get_path(attr)
                f.super_calls = utils.get_super_calls(self.__class__, attr)

                self.indent -= 1
                print(
                    f"{tab*self.indent} ({f.order}) Result: {attr.__qualname__} call is {res}"
                )

                return res

            return wrapper
        return attr
