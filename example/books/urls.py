from django.urls import path, include
from django.conf import settings

from . import views

app_name = 'books'

urlpatterns = [
    path("", views.BookListView.as_view(), name="books"),
    path("<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("edit/<int:pk>/", views.BookUpdateView.as_view(), name="book_edit"),
    path("delete/<int:pk>/", views.BookDeleteView.as_view(), name="book_delete"),
    path("new/", views.BookCreateView.as_view(), name="book_create"),
    path("authors/new/", views.AuthorCreateView.as_view(), name="author_create"),
    path("hello/", views.hello_html, name="hello"),
    path("hello_cbv/", views.HelloTest.as_view(), name="hello_cbv"),
    path("jsontest/", views.jsontest, name="jsontest"),
    path("gotobooks/", views.BookRedirect.as_view(), name="gotobooks"),
]

if settings.DEBUG:
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
