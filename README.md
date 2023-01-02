<h1 align="center">
    django-cbv-inspect
</h1>

<div align="center">
<a href="https://pypi.org/project/django-cbv-inspect/">
    <img src="https://img.shields.io/pypi/v/django-cbv-inspect?color=blue" alt="PyPI"/>
</a>
<a href="https://github.com/sjbitcode/django-cbv-inspect/actions/workflows/test.yml">
    <img src="https://github.com/sjbitcode/django-cbv-inspect/actions/workflows/test.yml/badge.svg?branch=master&event=push" alt="Test">
</a>
<a href="https://codecov.io/gh/sjbitcode/django-cbv-inspect" > 
    <img src="https://codecov.io/gh/sjbitcode/django-cbv-inspect/branch/master/graph/badge.svg?token=wAjvQLGtpd"/> 
</a>
<a href="https://pypi.org/project/django-cbv-inspect/">
    <img src="https://img.shields.io/pypi/pyversions/django-cbv-inspect" alt="python-versions">
</a>
<a href="https://pypi.org/project/django-cbv-inspect/">
    <img src="https://img.shields.io/pypi/frameworkversions/django/django-cbv-inspect.svg" alt="django-versions">
</a>
</div>

<br>

<div align="center">
    <p>A Django app to help inspect all class-based views within your Django project 🔎 ✨ </p>
    Inspired by django-debug-toolbar ❤️
</div>

<p align="center">
    <br>
    <img src="https://user-images.githubusercontent.com/6550256/210189547-b173d5a6-d69f-482e-b85b-5be31098610c.gif" alt="django-cbv-inspect demo"/>
</p>

<br>

---

<br>

## 📦 Installation
1. Install with pip
```
pip install django-cbv-inspect
```

2. Add `cbv_inspect` to your list of `INSTALLED_APPS` in your Django settings module
```python
INSTALLED_APPS = [
    ...
    "cbv_inspect",
    ...
]
```

3. Add the middleware to your list of `MIDDLEWARE` classes in your Django settings module
```python
MIDDLEWARE = [
    ...
    "cbv_inspect.middleware.DjCbvInspectMiddleware",
    ...
]
```

4. **Prerequisites**
    
    In your `TEMPLATES` settings within your Django settings module, make sure
   1. the `BACKEND` setting is `""django.template.backends.django.DjangoTemplates""`
   2. the `APP_DIRS` setting is `True`

<br>

---

<br>

## 🛞 Usage
When all installation steps are done, any html response rendered by a class-based view should display the `django-cbv-inspect` toolbar on the page.

By default, all class-based views will be processed by the middleware. If you wish to exclude views, there are two options:

### Exclude via mixin
```python
from cbv_inspect.mixins import DjCbvExcludeMixin


class MyCoolView(DjCbvExcludeMixin, View):
    pass
```


### Exclude via decorator
```python
from django.utils.decorators import method_decorator
from cbv_inspect.decorators import djcbv_exclude


@method_decorator(djcbv_exclude, name="dispatch")
class MyCoolView(View):
    pass
```

<br>

---

<br>

## 🧪 Run locally
You can run the `example` project locally to test things out!

Clone the project and from the root of the repo, run the following Make command to setup the `example` project:
```
make run-example
```

To run unittests with coverage, run
```
make coverage
```

<br>

---

<br>

## ⚡️ Features

The `django-cbv-inspect` toolbar has three main sections:

1. View information
2. CBV method call chain
3. MRO classes

<br>

### View information

This section shows high level information about the class-based view, request, and url.

<br>

### CBV method call chain

This is the main section that shows all methods that were excuted for the current class-based view:

It shows:
- method name and signature
- [Classy Class-Based Views (ccbv.co.uk)](https://ccbv.co.uk/) links
- method arguments and return value
- all resolved `super()` calls defined in the method
- module location


<br>

### MRO classes
This section lists all MRO classes of the current class-based view class. 

This can come in handy especially with the prior section when mapping the execution of a class-based view.

<br>

---

<br>

## ❓ Why did I build this?

Django class-based views are hard to grasp especially when you're new to Django.

Fortunately for us, tools like [django-debug-toolbar](https://github.com/jazzband/django-debug-toolbar) and [ccbv.co.uk](https://ccbv.co.uk/) are super helpful in providing extra context for debugging.

My goal for this app was to take what goes on under the hood in a class-based view and display it in an easy to use interface, just like what django-debug-toolbar does.

Hopefully this can help debug your class-based views!

Happy coding! ✨