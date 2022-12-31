import logging
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    RedirectView,
    View
)
from django.urls import reverse_lazy
from cbv_inspect.decorators import djcbv_exclude
from cbv_inspect.mixins import DjCbvExcludeMixin

from .forms import AuthorForm, BookForm
from .models import Author, Book


logger = logging.getLogger(__name__)


class FooMixin:
    def test(self):
        return 'Yo this is a test!'


class Coffee:
    def greet(self):
        return "yo"


# @method_decorator(djcbv_exclude, name='dispatch')
class BookListView(Coffee, FooMixin, ListView):
    # class BookListView(DjCbvExcludeMixin, Coffee, FooMixin, ListView):
    model = Book

    # @djcbv_exclude
    # def dispatch(self, request, *args, **kwargs):
    #     return super().dispatch(request, *args, **kwargs)

    def get_favorite_book(self):
        # logger.error('Getting favorite book!')
        return "Harry Potter"

    def get_context_data(self, **kwargs):
        """ a doctstring with super().omgomg() """
        context = super().get_context_data(**kwargs)
        context["now"] = "the time right now"
        # logger.error('In context data!')
        fav_book = self.get_favorite_book()

        context["fav_book"] = fav_book

        # ctx_object_name = super().get_context_object_name(Book.objects.all())
        # print(ctx_object_name)
        x = super(Coffee, self).test()
        # x = super().greet()

        # b = super().get_favorite_book()
        return context


# @djcbv_exclude
def hello(request):
    return HttpResponse('yo')


class HelloTest(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("hello from a CBV View!")


# @djcbv_exclude
def hello_html(request):
    books = Book.objects.all()
    authors = Author.objects.all()

    # from pprint import pformat

    book_str = str(books)
    author_str = str(authors)
    return render(request, 'books/hello.html', {})


# @djcbv_exclude
def hello_html2(request):
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
