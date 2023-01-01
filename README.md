<h1 align="center">
    django-cbv-inspect
</h1>

<p align="center">A tool to inspect all class-based views within your Django project 🔎 ✨ </p>

<p align="center">
    <br>
    <img src="example/cbv-inspect.gif" alt="demo gif"/>
</p>


---
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

---

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

---

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