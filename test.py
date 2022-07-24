from pprint import pprint

d = {1: {'args': "(<WSGIRequest: GET '/'>,)",
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.base/View/#setup',
              'children': {},
              'kwargs': '{}',
              'name': 'View.setup',
              'ordering': 1,
              'padding': 30,
              'path': '/django/views/generic/base.py',
              'ret_value': 'None',
              'tab_index': 1},
          2: {'args': "(<WSGIRequest: GET '/'>,)",
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.base/View/#dispatch',
              'children': {},
              'kwargs': '{}',
              'name': 'View.dispatch',
              'ordering': 2,
              'padding': 30,
              'path': '/django/views/generic/base.py',
              'ret_value': '<TemplateResponse status_code=200, "text/html; '
                           'charset=utf-8">',
              'tab_index': 1},
          3: {'args': "(<WSGIRequest: GET '/'>,)",
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/BaseListView/#get',
              'children': {},
              'kwargs': '{}',
              'name': 'BaseListView.get',
              'ordering': 3,
              'padding': 60,
              'path': '/django/views/generic/list.py',
              'ret_value': '<TemplateResponse status_code=200, "text/html; '
                           'charset=utf-8">',
              'tab_index': 2},
          4: {'args': '()',
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectMixin/#get_queryset',
              'children': {},
              'kwargs': '{}',
              'name': 'MultipleObjectMixin.get_queryset',
              'ordering': 4,
              'padding': 90,
              'path': '/django/views/generic/list.py',
              'ret_value': "<QuerySet [<Book: Harry Potter and the Sorcerer's "
                           'Stone>, <Book: Harry Potter and the Order of the '
                           'Pheonix>, <Book: The Witches>, <Book: A Game of '
                           'Thrones>, <Book: Harry Potter and the Chamber of '
                           'Secrets>, <Book: Test Book 1>]>',
              'tab_index': 3},
          5: {'args': '()',
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectMixin/#get_ordering',
              'children': {},
              'kwargs': '{}',
              'name': 'MultipleObjectMixin.get_ordering',
              'ordering': 5,
              'padding': 120,
              'path': '/django/views/generic/list.py',
              'ret_value': 'None',
              'tab_index': 4},
          6: {'args': '()',
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectMixin/#get_allow_empty',
              'children': {},
              'kwargs': '{}',
              'name': 'MultipleObjectMixin.get_allow_empty',
              'ordering': 6,
              'padding': 90,
              'path': '/django/views/generic/list.py',
              'ret_value': 'True',
              'tab_index': 3},
          7: {'args': '()',
              'ccbv_link': None,
              'children': {},
              'kwargs': '{}',
              'name': 'BookListView.get_context_data',
              'ordering': 7,
              'padding': 90,
              'path': '/Users/sangeeta/Code/cbv-introspect/example/books/views.py',
              'ret_value': "{'paginator': None, 'page_obj': None, "
                           "'is_paginated': False, 'object_list': <QuerySet "
                           "[<Book: Harry Potter and the Sorcerer's Stone>, "
                           '<Book: Harry Potter and the Order of the Pheonix>, '
                           '<Book: The Witches>, <Book: A Game of Thrones>, '
                           '<Book: Harry Potter and the Chamber of Secrets>, '
                           "<Book: Test Book 1>]>, 'book_list': <QuerySet "
                           "[<Book: Harry Potter and the Sorcerer's Stone>, "
                           '<Book: Harry Potter and the Order of the Pheonix>, '
                           '<Book: The Witches>, <Book: A Game of Thrones>, '
                           '<Book: Harry Potter and the Chamber of Secrets>, '
                           "<Book: Test Book 1>]>, 'view': "
                           '<books.views.BookListView object at 0x11ae895b0>, '
                           "'now': 'the time right now', 'fav_book': 'Harry "
                           "Potter'}",
              'tab_index': 3},
          8: {'args': "(<QuerySet [<Book: Harry Potter and the Sorcerer's "
                      'Stone>, <Book: Harry Potter and the Order of the '
                      'Pheonix>, <Book: The Witches>, <Book: A Game of '
                      'Thrones>, <Book: Harry Potter and the Chamber of '
                      'Secrets>, <Book: Test Book 1>]>,)',
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectMixin/#get_paginate_by',
              'children': {},
              'kwargs': '{}',
              'name': 'MultipleObjectMixin.get_paginate_by',
              'ordering': 8,
              'padding': 120,
              'path': '/django/views/generic/list.py',
              'ret_value': 'None',
              'tab_index': 4},
          9: {'args': "(<QuerySet [<Book: Harry Potter and the Sorcerer's "
                      'Stone>, <Book: Harry Potter and the Order of the '
                      'Pheonix>, <Book: The Witches>, <Book: A Game of '
                      'Thrones>, <Book: Harry Potter and the Chamber of '
                      'Secrets>, <Book: Test Book 1>]>,)',
              'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectMixin/#get_context_object_name',
              'children': {},
              'kwargs': '{}',
              'name': 'MultipleObjectMixin.get_context_object_name',
              'ordering': 9,
              'padding': 120,
              'path': '/django/views/generic/list.py',
              'ret_value': 'book_list',
              'tab_index': 4},
          10: {'args': '()',
               'ccbv_link': None,
               'children': {},
               'kwargs': '{}',
               'name': 'BookListView.get_favorite_book',
               'ordering': 10,
               'padding': 120,
               'path': '/Users/sangeeta/Code/cbv-introspect/example/books/views.py',
               'ret_value': 'Harry Potter',
               'tab_index': 4},
          11: {'args': "({'paginator': None, 'page_obj': None, 'is_paginated': "
                       "False, 'object_list': <QuerySet [<Book: Harry Potter "
                       "and the Sorcerer's Stone>, <Book: Harry Potter and the "
                       'Order of the Pheonix>, <Book: The Witches>, <Book: A '
                       'Game of Thrones>, <Book: Harry Potter and the Chamber '
                       "of Secrets>, <Book: Test Book 1>]>, 'book_list': "
                       "<QuerySet [<Book: Harry Potter and the Sorcerer's "
                       'Stone>, <Book: Harry Potter and the Order of the '
                       'Pheonix>, <Book: The Witches>, <Book: A Game of '
                       'Thrones>, <Book: Harry Potter and the Chamber of '
                       "Secrets>, <Book: Test Book 1>]>, 'view': "
                       '<books.views.BookListView object at 0x11ae895b0>, '
                       "'now': 'the time right now', 'fav_book': 'Harry "
                       "Potter'},)",
               'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.base/TemplateResponseMixin/#render_to_response',
               'children': {},
               'kwargs': '{}',
               'name': 'TemplateResponseMixin.render_to_response',
               'ordering': 11,
               'padding': 90,
               'path': '/django/views/generic/base.py',
               'ret_value': '<TemplateResponse status_code=200, "text/html; '
                            'charset=utf-8">',
               'tab_index': 3},
          12: {'args': '()',
               'ccbv_link': 'https://ccbv.co.uk/projects/Django/3.2/django.views.generic.list/MultipleObjectTemplateResponseMixin/#get_template_names',
               'children': {},
               'kwargs': '{}',
               'name': 'MultipleObjectTemplateResponseMixin.get_template_names',
               'ordering': 12,
               'padding': 120,
               'path': '/django/views/generic/list.py',
               'ret_value': "['books/book_list.html']",
               'tab_index': 4}}
