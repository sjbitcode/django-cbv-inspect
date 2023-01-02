import functools
import inspect
import logging
from typing import Any, List

from django.utils.decorators import method_decorator
from django.utils.functional import cached_property

from cbv_inspect import decorators, utils

logger = logging.getLogger("cbv_inspect.mixins")


class DjCbvInspectMixin:
    indent = 0
    order = 1

    @cached_property
    def allowed_callables(self) -> List:
        """
        Return list of all allowed methods.
        """
        cbv_funcs = list(
            filter(
                lambda x: not x[0].startswith("__"),
                inspect.getmembers(self.__class__, inspect.isfunction),
            )
        )
        return [func[0] for func in cbv_funcs]

    def __getattribute__(self, name: str) -> Any:
        attr = super().__getattribute__(name)

        if callable(attr) and name != "__class__" and name in self.allowed_callables:
            tab = "\t"
            log = utils.DjCbvLog()

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                logger.debug("%s (%s) %s", tab * self.indent, self.order, attr.__qualname__)

                log.order = self.order
                log.indent = self.indent

                request = utils.get_request(self, attr, *args)
                # if request not found, return attr lookup result
                if request is None:
                    return attr(*args, **kwargs)

                request._djcbv_inspect_metadata.logs[log.order] = log
                utils.set_log_parents(self.order, request)

                # Prep for next call
                self.indent += 1
                self.order += 1

                ret = attr(*args, **kwargs)

                log.name = attr.__qualname__
                log.args = utils.serialize_params(args)
                log.kwargs = utils.serialize_params(kwargs)
                log.return_value = utils.serialize_params(ret)
                log.signature = utils.get_signature(attr)
                log.path = utils.get_path(attr)
                log.super_calls = utils.get_super_calls(attr)
                log.ccbv_link = utils.get_ccbv_link(attr)

                self.indent -= 1

                logger.debug(
                    "%s (%s) result: %s",
                    tab * self.indent,
                    log.order,
                    log.return_value.replace("\n", ""),
                )

                return ret

            return wrapper
        return attr


class DjCbvExcludeMixin:
    @method_decorator(decorators.djcbv_exclude)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
