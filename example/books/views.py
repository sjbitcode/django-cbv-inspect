import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    RedirectView
)
from django.urls import reverse_lazy

from .forms import AuthorForm, BookForm
from .models import Author, Book


logger = logging.getLogger(__name__)


class FooMixin:
    def test(self):
        return 'Yo this is a test!'


class BookListView(FooMixin, ListView):
    model = Book

    def get_favorite_book(self):
        logger.error('Getting favorite book!')
        return "Harry Potter"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context["now"] = "the time right now"
    #     logger.error('In context data!')
    #     fav_book = self.get_favorite_book()
    #     context["fav_book"] = fav_book

    #     ctx_object_name = super().get_context_object_name(Book.objects.all())
    #     print(ctx_object_name)
    #     return context


def hello(request):
    return HttpResponse('yo')


def hello_html(request):
    return render(request, 'books/hello.html', {})


def jsontest(request):
    return JsonResponse({'foo': 'bar'})


class BookRedirect(RedirectView):
    url = reverse_lazy('books:books')


class BookDetailView(DetailView):
    model = Book


class BookCreateView(CreateView):
    model = Book
    form_class = BookForm


class BookUpdateView(UpdateView):
    model = Book
    form_class = BookForm

    def get_success_url(self) -> str:
        return reverse_lazy("books:book_detail", kwargs={"pk": self.object.pk})


class BookDeleteView(DeleteView):
    model = Book
    success_url = reverse_lazy("books:books")


class AuthorCreateView(CreateView):
    model = Author
    form_class = AuthorForm
    success_url = reverse_lazy("books:books")

