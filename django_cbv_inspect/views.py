import logging

from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def render_panel(request):
    # log_data = request.session.get('inspector_logs', {})

    log_data = {}
    request_metadata = {}
    error_msg = ''

    if hasattr(request, '_inspector_logs'):
        log_data = getattr(request, '_inspector_logs')
    logs = log_data.get('logs', {})  # {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}

    # check if path is correct
    if 'path' in log_data:
        if log_data['path'] !=  request.path:
            error_msg = f'{log_data["path"]} not equal to current path {request.path}'
            logger.error(error_msg)
            logs = {}
    
    # request metadata
    request_metadata['method'] = request.method
    request_metadata['path'] = request.get_full_path()
    request_metadata['body'] = request.POST.copy() or request.GET.copy()

    return render_to_string("django_cbv_inspect/cbv_logs.html", {
        'logs': dict(sorted(logs.items(), key=lambda item: item[0])),
        'message': 'yo',
        'error_msg': error_msg,
        'request_metadata': request_metadata
    })
