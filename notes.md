## Inspect what class `super` calls
- Use some regex to inspect a method definition, and see whether there's a super() call in it.
  - If its `super().` then call `super(BookListView.__mro__[2], self).get_context_data` where `__mro__[2]` refers to the first base class not including the InspectorMixin.
  - if its `super(blabla)`, then just see what that returns without calling the function, ex. `super(Foo, self).get_context_data`

## TODO:
- make separate package for inspector code
  - urls for template