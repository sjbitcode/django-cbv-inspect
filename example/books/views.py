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
        return 'Test from FooMixin'


class CoffeeMixin:
    def greet(self):
        return "Hello from CoffeeMixin"


# @method_decorator(djcbv_exclude, name='dispatch')  # test excluding this view
class BookListView(CoffeeMixin, FooMixin, ListView):
    model = Book

    def get_favorite_book(self):
        return "Harry Potter"

    def get_context_data(self, **kwargs):
        """ a doctstring with super().omgomg() """
        context = super().get_context_data(**kwargs)
        context["fav_book"] = self.get_favorite_book()

        super(CoffeeMixin, self).test()

        return context


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


class HelloCBV(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("hello from a CBV View!")


def hello_fbv(request):
    return render(request, 'books/hello.html', {})


def jsontest(request):
    return JsonResponse({'foo': 'bar'})
