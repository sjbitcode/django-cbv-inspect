def time_this(func):
    def wrapped(*args, **kwargs):
        print("_________timer starts_________")
        from datetime import datetime
        before = datetime.now()
        x = func(*args, **kwargs)
        after = datetime.now()
        print("** elapsed Time = {0} **\n".format(after - before))
        return x

    return wrapped


def time_all_class_methods(Cls):
    # decoration body - doing nothing really since we need to wait until the decorated object is instantiated
    class Wrapper:
        def __init__(self, *args, **kwargs):
            print(f"__init__() called with args: {args} and kwargs: {kwargs}")
            self.decorated_obj = Cls(*args, **kwargs)

        def __getattribute__(self, s):
            try:
                x = super().__getattribute__(s)
                return x
            except AttributeError:
                pass
            x = self.decorated_obj.__getattribute__(s)
            if type(x) == type(self.__init__):  # it is an instance method
                print(f"attribute belonging to decorated_obj: {x.__qualname__}")
                return time_this(x)  # this is equivalent of just decorating the method with time_this
            else:
                return x

    return Wrapper  # decoration ends here

class A:
    def foo(self):
        print('foo from A')

@time_all_class_methods
class MyClass(A):
    def __init__(self):
        import time
        print('entering MyClass.__init__')
        time.sleep(1.8)
        print("exiting MyClass.__init__")
    
    def foo(self):
        super().foo()
        print('foo from B')

    def method_x(self):
        print("entering MyClass.method_x")
        import time
        time.sleep(0.7)
        print("exiting MyClass.method_x")

    def method_y(self):
        print("entering MyClass.method_x")
        import time
        time.sleep(1.2)
        print("exiting MyClass.method_x")

instance = MyClass()

print("object created")
# instance.method_x()
# instance.method_y()
instance.foo()