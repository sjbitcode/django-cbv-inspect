## Inspect what class `super` calls
- Use some regex to inspect a method definition, and see whether there's a super() call in it.
  - If its `super().` then call `super(BookListView.__mro__[2], self).get_context_data` where `__mro__[2]` refers to the first base class not including the InspectorMixin.****
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
  
### 08/22
- add panel handler button
- when click handler button, show logs
- 


## Deadline - 09/02
- review backend logic
  - clean up middleware, mixin, view
- style logs
  - show toolbar to click and view logs ✅
    - organize panel page better? paneltitle and panelbody, sort out kinks there
  - css
- test!

## 10/9
- deadline obv not reached, watever...progress is GOOD!
- stringifying args, kwargs, return values
  - checking instance is ok, but what about nested objects that are querysets?
  - maybe do a regex replace when stringifying?
    - check for repr/str of queryset/request
- super() introspection via regex

## 10/13
- stringified args, kwargs, return values ✅
- fix scroll and fixed nav issue ✅
- need to do:
  - JS toggle args/kwargs/returnvalue for all (and individual?)
  - super() introspection


## 10/16
- super() introspection ✅
- JS toggle columns for all ✅
- need to do:
  - add ccbv link in "Base classes" column in View information section
  - fix +/- when toggle column visibility
  - add MRO? maybe underneath the Call chain section?

## 10/17
- add ccbv link in "Base classes" column in View information section ✅
- fix +/- when toggle column visibility ✅
- add MRO? maybe underneath the Call chain section? ✅
- need to do:
  - what do display when its a FBV? (like djdt "no GET data"?) ✅
  - plan cleanup
    - get rid of global dict and request session (all prior attempts of storing logs) ✅
    - inspect signature code can be cleaned up?
    - ccbv link, get module from inspect can be cleaned up? ✅
    - djCbv view plucking values from request._inspector_logs 😬
    - beautiful soup vs regex in middleware? ✅
    - take big picture look at:
      - mixin
      - middleware
      - view
      - template
    - write tests!

## djCBVInspect attributes
### aka `request._djcbv_inspect_metadata`

| Attribute | Panel Location | Description |
|-----------|-------------| ------------|
| path | View Information | request path, ex. `/books/1` |
| logs | CBV Call chain | dict of logs |
| view_path | View Information | dotpath of view class, ex. `books.views.BookListView` |
| url_name | View Information | url name, ex. `books:book_detail` |
| args | View Information | request args, ex. `()` |
| kwargs | View Information | request kwargs, ex. `{'pk': 1}` |
| base_classes | View Information | dict with base class info, `name` and `ccbv_link` |
| mro | MRO | dict with MRO classes, `name` and `ccbv_link` |
| method | View Information | request method, ex. `GET` |


## 10/25
- did some cleanup...
- should Mixin be removed from CBV bases in middleware?
- django rest framework support for ccbv_links?