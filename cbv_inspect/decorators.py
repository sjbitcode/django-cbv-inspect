from functools import partial, wraps
from typing import Callable


def djcbv_exclude(view_func: Callable) -> Callable:
    """
    Attach a `djcbv_exclude` attribute to the incoming view function,
    so it can get excluded by DjCbvInspectMiddleware.
    """

    # We don't need to attach our attribute to the partial function
    # that Django `method_decorator` creates to have a bound function.
    # We need to attach our attribute to the decorated wrapper function
    # so that it gets inspected by the middleware before the view runs,
    # i.e. MyViewClass.dispatch function
    # Django's as_view() function then updates the returned view func with
    # attributes set by decorators on the dispatch function...this is how
    # our attribute gets exposed to the middleware.
    if not isinstance(view_func, partial):
        setattr(view_func, "djcbv_exclude", True)

    @wraps(view_func)
    def _wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    return _wrapped_view
