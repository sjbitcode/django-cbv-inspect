class AncientFoo:
    def greet(self):
        return "Hello, from ancient foo!"


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


class FuturisticFoo(Foo):
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
