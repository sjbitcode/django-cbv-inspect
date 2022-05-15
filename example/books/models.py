import random
import string

from django.db import models
from django.db.models.signals import pre_save
from django.urls import reverse


class Book(models.Model):
    name = models.CharField(max_length=100)
    author = models.ForeignKey("Author", on_delete=models.CASCADE)
    published = models.DateField()
    isbn = models.CharField(max_length=17, blank=True)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("books:book_detail", kwargs={"pk": self.pk})


class Author(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    @property
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return self.name


# Create a digit with of length x
d = lambda x: "".join(random.choice(string.digits) for _ in range(x))


def generate_isbn(sender, instance, *args, **kwargs):
    print(sender, instance)
    if not instance.isbn:
        instance.isbn = f"{d(3)}-{d(1)}-{d(2)}-{d(6)}-{d(1)}"


pre_save.connect(generate_isbn, sender=Book)
