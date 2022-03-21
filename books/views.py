from dataclasses import dataclass, field
import inspect
import functools
from typing import Any
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
from django.utils.functional import cached_property

# from django.utils.decorators import method_decorator

from .forms import AuthorForm, BookForm
from .models import Author, Book


INSPECT_LOGS = {}

@dataclass
class FunctionLog:
    tab_index: int = 0
    ordering: int = 0
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    name: str = None
    ret_value: Any = None


class InspectorMixin:
    tab_index = 0
    func_order = 0

    @cached_property
    def get_whitelisted_callables(self):
        cbv_funcs = list(
            filter(
                lambda x: not x[0].startswith("__"),
                inspect.getmembers(self.__class__, inspect.isfunction),
            )
        )
        return [func[0] for func in cbv_funcs]

    def __getattribute__(self, name: str):
        attr = super().__getattribute__(name)

        if (
            callable(attr)
            and name != "__class__"
            and attr.__name__ in self.get_whitelisted_callables
        ):
            tab = "\t"
            f = FunctionLog()

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                print(f"{tab*self.tab_index} QUALNAME --> {attr.__qualname__}")
                print(
                    f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                )
                print(f"{tab*self.tab_index} FUNC ORDER --> ", self.func_order)
                # print(inspect.getsource(attr))
                # print(inspect.getframeinfo(inspect.currentframe()).function)
                self.tab_index += 1
                self.func_order += 1
                f.ordering = self.func_order

                res = attr(*args, **kwargs)
                # print(
                #     f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                # )

                # Update function log
                f.name = attr.__qualname__
                f.tab_index = self.tab_index
                f.args = args
                f.kwargs = kwargs
                f.ret_value = res

                global INSPECT_LOGS
                INSPECT_LOGS[f.ordering] = f

                self.tab_index -= 1
                print(
                    f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                )
                print(f"{tab*self.tab_index} After calling {attr.__qualname__}\n")
                return res

            return wrapper
        return attr

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

