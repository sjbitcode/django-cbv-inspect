from django.urls import path

from . import views

urlpatterns = [
    path("", views.BookListView.as_view(), name="books"),
    path("<int:pk>/", views.BookDetailView.as_view(), name="book_detail"),
    path("edit/<int:pk>/", views.BookUpdateView.as_view(), name="book_edit"),
    path("new/", views.BookCreateView.as_view(), name="book_create"),
    path("authors/new/", views.AuthorCreateView.as_view(), name="author_create"),
]
