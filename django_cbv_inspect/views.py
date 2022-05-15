import logging

from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def render_panel(request):
    log_data = request.session.get('inspector_logs', {})
    error_msg = ''

    # check if path is correct
    if 'path' in log_data:
        if log_data['path'] !=  request.path:
            stored_path = log_data['path']
            error_msg = f'{stored_path} not equal to current path {request.path}'
            logger.error(error_msg)

    logs = log_data.get('logs', {})

    return render_to_string("django_cbv_inspect/cbv_logs.html", {'logs': logs, 'message': 'yo', 'error_msg': error_msg})
