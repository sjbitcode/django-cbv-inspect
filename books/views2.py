import inspect
import functools

from django.shortcuts import render
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy

# from django.utils.decorators import method_decorator

from .forms import AuthorForm, BookForm
from .models import Author, Book


# def inspect_cbv(func):
#     def decorator__init(self, *args, **kwargs):
#         print("Decorator running")
#         # print(args, kwargs)
#         # return func(*args, **kwargs)

#     func.__init__ = decorator__init
#     return decorator__init

INSPECT_LOGS = {}

# import sys


# def trace(frame, event, arg):
#     if event == "call":
#         filename = frame.f_code.co_filename
#         if filename == "/path/to/file":
#             lineno = frame.f_lineno
#             # Here I'm printing the file and line number,
#             # but you can examine the frame, locals, etc too.
#             print("%s @ %s" % (filename, lineno))
#     return trace


# sys.settrace(trace)
# sys.settrace(None)


class InspectorMixin:
    tab_index = 0

    @property
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

            @functools.wraps(attr)
            def wrapper(*args, **kwargs):
                print(f"{tab*self.tab_index} QUALNAME --> {attr.__qualname__}")
                print(
                    f"{tab*self.tab_index} Before calling {attr.__qualname__} with args {args} and kwargs {kwargs}"
                )
                # print(inspect.getsource(attr))
                # print(inspect.getframeinfo(inspect.currentframe()).function)
                self.tab_index += 1

                res = attr(*args, **kwargs)
                print(
                    f"{tab*self.tab_index} Result of {attr.__qualname__} call is {res}"
                )

                self.tab_index -= 1
                print(f"{tab*self.tab_index} After calling {attr.__qualname__}")
                return res

            return wrapper
        return attr


# ListView.__getattribute__ = InspectorMixin.__getattribute__
# for cls in ListView.mro():
#     if cls.__name__ != "object":
#         cls.__getattribute__ = InspectorMixin.__getattribute__


class BookListView(InspectorMixin, ListView):
    model = Book

    # def get_context_data(self, **kwargs):
    #     x = 1
    #     context = super(BookListView, self).get_context_data(**kwargs)
    #     context["now"] = "the time right now"
    #     return context


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
