## Inspect what class `super` calls
- Use some regex to inspect a method definition, and see whether there's a super() call in it.
  - If its `super().` then call `super(BookListView.__mro__[2], self).get_context_data` where `__mro__[2]` refers to the first base class not including the InspectorMixin.
  - if its `super(blabla)`, then just see what that returns without calling the function, ex. `super(Foo, self).get_context_data`

```
>>> from books.views import BookListView
>>> BookListView.__mro__
(<class 'books.views.BookListView'>, <class 'books.views.FooMixin'>, <class 'django.views.generic.list.ListView'>, <class 'django.views.generic.list.MultipleObjectTemplateResponseMixin'>, <class 'django.views.generic.base.TemplateResponseMixin'>, <class 'django.views.generic.list.BaseListView'>, <class 'django.views.generic.list.MultipleObjectMixin'>, <class 'django.views.generic.base.ContextMixin'>, <class 'django.views.generic.base.View'>, <class 'object'>)
>>>
>>> BookListView.__bases__
(<class 'books.views.FooMixin'>, <class 'django.views.generic.list.ListView'>)
>>>
>>> BookListView.__bases__[-1]
<class 'django.views.generic.list.ListView'>
>>>
>>> super(BookListView.__bases__[-1], BookListView()).get_context_data
<bound method MultipleObjectMixin.get_context_data of <books.views.BookListView object at 0x102bea940>>
```

## TODO:
- make separate package for inspector code
  - urls for template

## UPDATE 4/18
- rendered an h1 with BeautifulSoup from middleware

### TODO:
- add JS to toggle hidden state ✅
- create inspector base html like debug_toolbar, include JS in there
- JS things:
  - click to show full screen
  - close full screen to hidden
  - structure of logs
- render to string

### 05/15
- restructured cbv_inspect outside of examples folder with django test project inside there
- do setup.py stuff
- pip install -e ../ on a project with user login to see if it records logs when a user is logging in/logging out!
  - uploaded to test PyPi but keep getting issues with beautiful soup :(
`python -m build && twine upload -r testpypi dist/* --verbose`

### 06/5
- nested log divs!! YES!!!!!!!!!! (blue border)
- need to do accordian thing, show result at bottom of div. Sort out how to show log content.
- nested divs with prepared divs templated, so JS only does nesting. (green border)

### 07/24
- working toggle buttons
- JS links
  - https://bobbyhadz.com/blog/javascript-get-element-by-data-attribute

## Deadline - 09/02
- review backend logic
  - clean up middleware, mixin, view
- style logs
  - show toolbar to click and view logs
  - css
- test!