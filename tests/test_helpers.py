from django.views.generic import View

from django_cbv_inspect import mixins


class AncientFoo:
    def greet(self):
        return "Hello, from ancient foo!"

    def customize_greet(self, name):
        return f"Hello, {name}"

    def greet_in_spanish(self):
        return "Hola, from ancient foo!"


class Foo(AncientFoo):
    color = "red"

    def greet(self):
        super().greet()
        return "Hello, from foo!"

    def goodbye(self):
        return "Goodbye, from foo!"

    @classmethod
    def get_cls_color(cls):
        return cls.color

    @staticmethod
    def get_number():
        return 4


class MixinFoo():
    def some_random_method(self):
        return 1


class FuturisticFoo(MixinFoo, Foo):
    def customize_greet(self, name):
        greeting = super().customize_greet(name)
        return f"{greeting}!!!"

    def excited_spanish_greet(self):
        greeting = super().greet_in_spanish()
        return greeting.upper()

    def test(self):
        """ this method will error if called! """
        super().some_nonexistent_method()


class DjFoo(mixins.DjCbvInspectMixin, FuturisticFoo):
    pass


def sample_func():
    """
    Sample docstring!
    """
    x = 1  # comment 1

    # comment 2

    return x


def sample_func2():
    return 1


class AwesomeMixin():
    def do_some_django_thing(self, *args, **kwargs):
        pass
