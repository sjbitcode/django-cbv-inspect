from django.forms import ModelForm

from .models import Author, Book


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = ["name", "author", "published"]


class AuthorForm(ModelForm):
    class Meta:
        model = Author
        fields = "__all__"
