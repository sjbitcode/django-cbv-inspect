from django.http import HttpResponse

from django.shortcuts import render
from django.views.generic import (
    View,
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy

from .forms import AuthorForm, BookForm
from .models import Author, Book


class FooMixin:
    def test(self):
        return 'Yo this is a test!'


class BookListView(FooMixin, ListView):
    model = Book

    def get_favorite_book(self):
        return "Harry Potter"

    def get_context_data(self, **kwargs):
        # import pdb; pdb.set_trace()
        x = 1
        context = super().get_context_data(**kwargs)
        context["now"] = "the time right now"
        fav_book = self.get_favorite_book()
        context["fav_book"] = fav_book
        return context


def hello(request):
    return HttpResponse('yo')


class BookDetailView(DetailView):
    model = Book


class BookCreateView(CreateView):
    model = Book
    form_class = BookForm


class BookUpdateView(UpdateView):
    model = Book
    form_class = BookForm

    def get_success_url(self) -> str:
        return reverse_lazy("book_detail", kwargs={"pk": self.object.pk})


class BookDeleteView(DeleteView):
    model = Book
    success_url = reverse_lazy("books")


class AuthorCreateView(CreateView):
    model = Author
    form_class = AuthorForm
    success_url = reverse_lazy("books")

