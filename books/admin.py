from django.contrib import admin

from .models import Author, Book


admin.site.register(Author)
admin.site.register(Book)
