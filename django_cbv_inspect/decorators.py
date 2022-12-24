from functools import partial, wraps


def djcbv_exclude(view_func):
    if not isinstance(view_func, partial):
        print(f'👁 {view_func}')
        setattr(view_func, 'djcbv_exclude', True)
        print(f'✅ ✅ ✅ {view_func.djcbv_exclude}')

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return _wrapped_view
