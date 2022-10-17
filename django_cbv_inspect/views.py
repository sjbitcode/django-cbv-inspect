import logging

from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


def render_panel(request):
    # log_data = request.session.get('inspector_logs', {})

    log_data = {}
    request_metadata = {}
    error_msg = ""

    if hasattr(request, "_inspector_logs"):
        log_data = getattr(request, "_inspector_logs")

    logs = log_data.get("logs", {})  # {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
    view_path = log_data.get("view_path")
    url_name = log_data.get('url_name')
    args = log_data.get('args')
    kwargs = log_data.get('kwargs')
    base_classes = log_data.get('base_classes')
    mro = log_data.get("mro")

    # check if path is correct
    if "path" in log_data:
        if log_data["path"] != request.path:
            error_msg = f'{log_data["path"]} not equal to current path {request.path}'
            logger.error(error_msg)
            logs = {}

    # request metadata
    request_metadata["method"] = request.method
    request_metadata["path"] = request.get_full_path()
    request_metadata["body"] = request.POST.copy() or request.GET.copy()

    # sort logs
    sorted_logs = dict(sorted(logs.items(), key=lambda item: item[0]))

    # add is_parent log attributes
    # for key, val in sorted_logs.items():
    #     try:
    #         next_log = sorted_logs[key + 1]
    #         if val['tab_index'] < next_log['tab_index']:
    #             val['is_parent'] = 1
    #         else:
    #             val['is_parent'] = 0
    #     except KeyError:
    #         pass

    # attach parent ids to children

    lowest_tab = (1, 0)  # key, tab
    for key, val in sorted_logs.items():
        try:
            # establish the lowest tab
            if val['tab_index'] <= lowest_tab[1]:
                lowest_tab = (key, val['tab_index'])
            print(lowest_tab)

            next_log = sorted_logs[key + 1]

            # if next log is a child of current log
            if val['tab_index'] < next_log['tab_index']:
                val['is_parent'] = 1

                next_log["parent"] = f"cbvInspect_{val['ordering']}_{val['tab_index']}"

                # transfer parents of current log to next log
                if val.get('parent'):
                    next_log['parent'] = f"{val['parent']} {next_log['parent']}"
            # if next log is NOT a child of current log, find ancestors!
            else:
                val['is_parent'] = 0

                ancestors = list(range(lowest_tab[0], next_log['ordering']))

                # find the closest ancestor whose a parent and copy their parents if they have, and set parent on next_log
                for k2 in ancestors[::-1]:
                    if sorted_logs[k2]['tab_index'] < next_log['tab_index']:
                        if sorted_logs[k2]['is_parent']:

                            # get that log's parents
                            if 'parent' in sorted_logs[k2]:
                                ancestor = sorted_logs[k2]['parent']

                            next_log['parent'] = f"{ancestor} cbvInspect_{sorted_logs[k2]['ordering']}_{sorted_logs[k2]['tab_index']}"
                            break
        except KeyError:
            pass
    # curr_tab_index = 0
    # for key, val in sorted_logs.items():
    #     try:
    #         # if current log's tab is less than stored current tab
    #         if val['tab_index'] < curr_tab_index:
    #             curr_tab_index = val['tab_index']

    #         print(key, curr_tab_index)

    #     except KeyError:
    #         pass

    return render_to_string(
        "django_cbv_inspect/cbv_logs2.html",
        {
            "logs": sorted_logs,
            "message": "yo",
            "error_msg": error_msg,
            "request_metadata": request_metadata,
            "view_path": view_path,
            "url_name": url_name,
            "args": args,
            "kwargs": kwargs,
            "base_classes": base_classes,
            "mro": mro,
        },
    )
