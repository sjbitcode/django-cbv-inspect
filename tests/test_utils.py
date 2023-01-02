import inspect
import unittest
from collections import namedtuple
from unittest.mock import MagicMock, Mock, create_autospec, patch

from django import get_version
from django.test import RequestFactory, TestCase
from django.views.generic import TemplateView

from cbv_inspect.mixins import DjCbvInspectMixin
from cbv_inspect.utils import (
    DjCbvClassOrMethodInfo,
    DjCbvException,
    DjCbvLog,
    class_has_method,
    collect_parent_classes,
    get_bases,
    get_callable_source,
    get_ccbv_link,
    get_mro,
    get_path,
    get_request,
    get_signature,
    get_sourcecode,
    get_super_calls,
    is_cbv_view,
    mask_queryset,
    mask_request,
    serialize_params,
    set_log_parents,
)

from . import models, test_helpers, views

SubTestArgs = namedtuple("SubTestArgs", "passed expected")


class TestIsViewCbv(unittest.TestCase):
    """
    Tests for the `is_cbv_view` util function.
    """

    def test_is_view_cbv_returns_true_for_cbv_func(self):
        """
        Test that the view function for a class-based view.
        """

        # Arrange
        view_func = views.RenderHtmlView.as_view()

        # Act
        from_cbv = is_cbv_view(view_func)

        # Assert
        self.assertTrue(from_cbv)

    def test_is_view_cbv_returns_false_for_fbv(self):
        """
        Test a function-based view function.
        """

        # Arrange
        view_func = views.fbv_render

        # Act
        from_cbv = is_cbv_view(view_func)

        # Assert
        self.assertFalse(from_cbv)


class TestCollectParentClasses(unittest.TestCase):
    """
    Tests for the `collect_parent_classes` util function.
    """

    def test_collect_parent_classes_returns_metadata_for_mro(self):
        """
        Test that an mro lookup returns a list of `DjCbvClassOrMethodInfo` objects.
        """

        # Arrange
        mro = test_helpers.FuturisticFoo.__mro__
        mro_cls_metadata = []

        for mro_cls in mro:
            mro_cls_metadata.append(
                DjCbvClassOrMethodInfo(
                    ccbv_link=None, name=f"{mro_cls.__module__}.{mro_cls.__name__}", signature=None
                )
            )

        # Act
        cls_metadata = collect_parent_classes(test_helpers.FuturisticFoo, "__mro__")
        cls_metadata_from_mro = get_mro(test_helpers.FuturisticFoo)

        # Assert
        self.assertEqual(mro_cls_metadata, cls_metadata)
        self.assertEqual(mro_cls_metadata, cls_metadata_from_mro)

    def test_collect_parent_classes_returns_metadata_for_bases(self):
        """
        Test that a bases class lookup returns a list of `DjCbvClassOrMethodInfo` objects.
        """

        # Arrange
        bases = test_helpers.FuturisticFoo.__bases__
        base_cls_metadata = []

        for base_cls in bases:
            base_cls_metadata.append(
                DjCbvClassOrMethodInfo(
                    ccbv_link=None,
                    name=f"{base_cls.__module__}.{base_cls.__name__}",
                    signature=None,
                )
            )

        # Act
        cls_metadata = collect_parent_classes(test_helpers.FuturisticFoo, "__bases__")
        cls_metadata_from_get_bases = get_bases(test_helpers.FuturisticFoo)

        # Assert
        self.assertEqual(base_cls_metadata, cls_metadata)
        self.assertEqual(base_cls_metadata, cls_metadata_from_get_bases)

    def test_collect_parent_classes_skips_djcbvinspectmixin(self):
        """
        Test that the `DjCbvInspectMixin` class gets filtered out from result list.
        """

        # Arrange
        bases = test_helpers.DjFoo.__bases__
        base_cls_metadata = []

        for base_cls in bases:
            if base_cls is not DjCbvInspectMixin:
                base_cls_metadata.append(
                    DjCbvClassOrMethodInfo(
                        ccbv_link=None,
                        name=f"{base_cls.__module__}.{base_cls.__name__}",
                        signature=None,
                    )
                )

        # Act
        cls_metadata = collect_parent_classes(test_helpers.DjFoo, "__bases__")
        cls_metadata_from_get_bases = get_bases(test_helpers.DjFoo)

        # Assert
        self.assertEqual(base_cls_metadata, cls_metadata)
        self.assertEqual(base_cls_metadata, cls_metadata_from_get_bases)


class TestGetCCBVLink(unittest.TestCase):
    """
    Tests for the `get_ccbv_link` util function.
    """

    def test_ccbv_link_returns_link_for_cbv_cls(self):
        """
        Test that a ccbv link is generated for a Django generic view.
        """

        # Arrange
        version: str = get_version().rsplit(".", 1)[0]
        module: str = TemplateView.__module__
        expected_ccbv_url = (
            f"https://ccbv.co.uk/projects/Django/{version}/{module}/{TemplateView.__name__}"
        )

        # Act
        ccbv_url = get_ccbv_link(TemplateView)

        # Assert
        self.assertEqual(expected_ccbv_url, ccbv_url)

    def test_ccbv_link_returns_link_for_cbv_method(self):
        """
        Test that a ccbv link is generated for a Django generic view method.
        """

        # Arrange
        cbv_method = TemplateView.get_template_names

        version: str = get_version().rsplit(".", 1)[0]
        module: str = TemplateView.__module__
        class_name, method_name = cbv_method.__qualname__.rsplit(".", 1)
        expected_ccbv_url = (
            f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"
        )

        # Act
        ccbv_url = get_ccbv_link(cbv_method)

        # Assert
        self.assertEqual(expected_ccbv_url, ccbv_url)

    @patch.object(inspect, "isclass", return_value=False)
    def test_ccbv_link_does_not_return_link_for_cbv_nonclass(self, _):
        """
        Test that no ccbv link is generated for a nonclass or nonmethod object.
        """

        # Arrange
        mock_obj = Mock()
        mock_obj.__module__ = TemplateView.__module__

        # Act
        ccbv_url = get_ccbv_link(mock_obj)

        # Assert
        self.assertEqual(None, ccbv_url)

    def test_ccbv_link_does_not_return_link_for_local_cbv_cls(self):
        """
        Test that no ccbv link is generated for a user-defined cbv class.
        """

        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView))

    def test_ccbv_link_does_not_return_link_for_local_cbv_method(self):
        """
        Test that no ccbv link is generated for an overriden cbv method.
        """

        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView.get_context_data))


@patch.object(inspect, "getfile")
class TestGetPath(unittest.TestCase):
    """
    Tests for the `get_path` util function.
    """

    def test_get_path_for_dependency_returns_truncated_path(self, mock_getfile):
        """
        Test path for an installed package.
        """

        # Arrange
        mock_getfile.return_value = "some/path/site-packages/cool/cool_class.py"
        expected_return_path = "/cool/cool_class.py"

        # Act
        path = get_path(Mock())

        # Assert
        self.assertEqual(expected_return_path, path)

    def test_get_path_for_internal_dependency_returns_full_path(self, mock_getfile):
        """
        Test path for an internal module.
        """

        # Arrange
        mock_getfile.return_value = "some/path/cool/cool_class.py"

        # Act
        path = get_path(Mock())

        # Assert
        self.assertEqual(mock_getfile.return_value, path)


class TestSerializeParams(unittest.TestCase):
    """
    Tests for the `serialize_params` util function.
    """

    @patch("cbv_inspect.utils.mask_request")
    @patch("cbv_inspect.utils.mask_queryset")
    @patch("cbv_inspect.utils.pformat")
    def test_serialize_params_calls_pformat_and_clean_functions(
        self, mock_pformat, mock_mask_queryset, mock_mask_req
    ):
        """
        Test that formatting and clean functions run.
        """

        # Act
        serialize_params({"name": "Foo"})

        # Assert
        mock_pformat.assert_called_once()
        mock_mask_req.assert_called_once()
        mock_mask_queryset.assert_called_once()


class TestMaskRequest(unittest.TestCase):
    """
    Tests for the `mask_request` util function.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_mask_request_replaces_string_correctly(self):
        """
        Test that only HttpRequest objects are masked.
        """

        # Arrange
        expected = "<<request>>"

        args = [
            SubTestArgs(passed=str(self.factory.get("")), expected=expected),
            SubTestArgs(passed=str(self.factory.get("/foo")), expected=expected),
            SubTestArgs(passed=str((1, 2)), expected="(1, 2)"),
            SubTestArgs(passed=" ", expected=" "),
            SubTestArgs(passed="", expected=""),
        ]

        # Act/Assert
        for arg in args:
            with self.subTest(arg):
                masked = mask_request(arg.passed)
                self.assertEqual(arg.expected, masked)


class TestMaskQueryset(TestCase):
    """
    Tests for the `mask_queryset` util function.
    """

    def setUp(self):
        self.model = models.Book
        self.model.objects.create(name="The Witches")
        self.model.objects.create(name="Harry Potter and the Chamber of Apps")

    def test_mask_queryset_replaces_string_correctly(self):
        """
        Test that only QuerySet objects are masked.
        """

        # Arrange
        expected = "<<queryset>>"

        non_empty_qs = SubTestArgs(passed=str(self.model.objects.all()), expected=expected)
        self.model.objects.all().delete()
        empty_qs = SubTestArgs(passed=str(self.model.objects.all()), expected=expected)

        args = [
            non_empty_qs,
            empty_qs,
            SubTestArgs(passed=str((1, 2)), expected="(1, 2)"),
            SubTestArgs(passed=" ", expected=" "),
            SubTestArgs(passed="", expected=""),
        ]

        # Act/Assert
        for arg in args:
            with self.subTest(arg):
                masked = mask_queryset(arg.passed)
                self.assertEqual(arg.expected, masked)


class TestGetSignature(unittest.TestCase):
    """
    Tests for the `get_signature` util function.
    """

    def test_signature_for_bound_method(self):
        """
        Test that the signature returned contains "self" for bound methods.
        """
        # Arrange
        m = test_helpers.FuturisticFoo().customize_greet

        # Act
        sig = get_signature(m)

        # Assert
        self.assertEqual(str(inspect.signature(m)), "(name)")
        self.assertEqual(sig, "(self, name)")

    def test_signature_for_unbound_method(self):
        """
        Test that the signature returned is expected for unbound methods.
        """
        # Arrange
        f = test_helpers.FuturisticFoo.customize_greet

        # Act
        sig = get_signature(f)

        # Assert
        self.assertEqual(str(inspect.signature(f)), "(self, name)")
        self.assertEqual(sig, "(self, name)")


class TestGetCallableSource(unittest.TestCase):
    """
    Tests for the `get_callable_source` util function.
    """

    def test_get_callable_source_for_method_returns_class(self):
        """
        Test that the source of a method defined on a class returns that class.
        """

        # Arrange
        foo_cls = test_helpers.Foo

        # Act
        source = get_callable_source(foo_cls.goodbye)

        # Assert
        self.assertEqual(source, foo_cls)

    def test_get_callable_source_for_inherited_method_returns_parent_class(self):
        """
        Test that the source of an inherited method returns the base class that defines it.
        """

        # Arrange
        foo_cls = test_helpers.Foo

        # Act
        source = get_callable_source(foo_cls.greet_in_spanish)

        # Assert
        self.assertNotEqual(source, foo_cls)

    def test_get_callable_source_for_overriden_method_returns_overriding_class(self):
        """
        Test that the source of an overridden method returns the class that overrides it.
        """

        # Arrange
        foo_cls = test_helpers.Foo

        # Act
        source = get_callable_source(foo_cls.greet)  # Foo's superclass also defines greet

        # Assert
        self.assertEqual(source, foo_cls)

    def test_get_callable_source_for_function_returns_the_function(self):
        """
        Test that the source of a function is the function itself.
        """

        # Arrange
        func = test_helpers.sample_func2

        # Act
        source = get_callable_source(func)  # Foo's superclass also defines greet

        # Assert
        self.assertEqual(source, func)


class TestClassHasMethod(unittest.TestCase):
    """
    Tests for the `class_has_method` util function.
    """

    def test_class_has_method_returns_true_for_method(self):
        """
        Test a class method.
        """

        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.Foo, "greet"))

    def test_class_has_method_returns_false_for_attribue(self):
        """
        Test a class attribute.
        """

        # Act/Assert
        self.assertFalse(class_has_method(test_helpers.Foo, "color"))

    def test_class_has_method_returns_false_for_nonexistent_method(self):
        """
        Test an undefined method.
        """

        # Act/Assert
        self.assertFalse(class_has_method(test_helpers.Foo, "some_method"))

    def test_class_has_method_returns_true_for_inherited_method(self):
        """
        Test an inherited method.
        """

        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "greet"))

    def test_class_has_method_returns_true_for_classmethod(self):
        """
        Test a classmethod.
        """

        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "get_cls_color"))

    def test_class_has_method_returns_true_for_staticmethod(self):
        """
        Test a staticmethod.
        """

        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "get_number"))

    def test_class_has_method_returns_false_for_property(self):
        """
        Test a property.
        """

        # Act/Assert
        self.assertFalse(class_has_method(test_helpers.Foo, "uppercase_color"))


class TestGetSourcecode(unittest.TestCase):
    """
    Tests for the `get_sourcecode` util function.
    """

    def test_get_sourcecode_strips_docstring(self):
        """
        Test that docstring and comments are removed.
        """

        # Act
        sourcecode = get_sourcecode(test_helpers.sample_func)

        # Assert
        self.assertFalse("Sample docstring" in sourcecode)
        self.assertFalse("comment" in sourcecode)
        self.assertFalse("#" in sourcecode)

    def test_get_sourcecode_for_func_witout_docstring_or_comments(self):
        """
        Test with function that has no docstring or comments.
        """

        # Act
        sourcecode = get_sourcecode(test_helpers.sample_func2)

        # Assert
        self.assertFalse("#" in sourcecode)
        self.assertEqual(sourcecode, inspect.getsource(test_helpers.sample_func2))


class TestGetSuperCalls(unittest.TestCase):
    """
    Test the `get_super_calls` util function.
    """

    def test_method_with_no_super_returns_none(self):
        """
        Test a class method that has no super calls.
        """

        # Arrange
        instance = test_helpers.Foo()  # we need to pass in the bound method

        # Act
        super_calls = get_super_calls(instance.goodbye)

        # Assert
        self.assertIsNone(super_calls)

    def test_super_call_that_resolves_to_direct_parent(self):
        """
        Test a class method with a super call that resolves to a base class method.
        """

        # Arrange
        instance = test_helpers.Foo()
        expected_super_call = DjCbvClassOrMethodInfo(
            ccbv_link=None,
            name=test_helpers.AncientFoo.greet.__qualname__,
            signature=str(inspect.signature(test_helpers.AncientFoo.greet)),
        )

        # Act
        super_calls = get_super_calls(instance.greet)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_that_resolves_to_ancestor(self):
        """
        Test a class method with a super call that resolves to one of its mro classes
        (not a direct base class).
        """

        # Arrange
        instance = test_helpers.FuturisticFoo()
        expected_super_call = DjCbvClassOrMethodInfo(
            ccbv_link=None,
            name=test_helpers.AncientFoo.customize_greet.__qualname__,
            signature=str(inspect.signature(test_helpers.AncientFoo.customize_greet)),
        )

        # Act
        super_calls = get_super_calls(instance.customize_greet)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_that_does_not_resolve(self):
        """
        Test a class method with a super call to a nonexistent method.
        """

        # Arrange
        instance = test_helpers.FuturisticFoo()
        expected_super_call = {}

        # Act
        super_calls = get_super_calls(instance.test)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_for_different_method_than_calling_method(self):
        """
        Test a class method with a multiple super calls.
        """

        # Arrange
        instance = test_helpers.FuturisticFoo()
        expected_super_calls = [
            DjCbvClassOrMethodInfo(
                ccbv_link=None,
                name=test_helpers.AncientFoo.greet_in_spanish.__qualname__,
                signature=str(inspect.signature(test_helpers.AncientFoo.greet_in_spanish)),
            ),
            DjCbvClassOrMethodInfo(
                ccbv_link=None,
                name=test_helpers.Foo.get_number.__qualname__,
                signature=str(inspect.signature(test_helpers.Foo.get_number)),
            ),
        ]

        # Act
        super_calls = get_super_calls(instance.excited_spanish_greet)

        # Assert
        self.assertEqual(2, len(super_calls))
        self.assertEqual(expected_super_calls[0], super_calls[0])
        self.assertEqual(expected_super_calls[1], super_calls[1])


class TestGetRequest(unittest.TestCase):
    """
    Tests for the `get_request` util function.
    """

    def test_get_request_from_setup(self):
        """
        Test retrieving request from View.setup method.
        """

        # Arrange
        request = RequestFactory().get("/")
        cbv_instance = create_autospec(views.HelloTest)
        cbv_method = MagicMock()
        cbv_method.__name__ = "setup"

        # Act
        returned_request = get_request(cbv_instance, cbv_method, request)

        # Assert
        self.assertEqual(request, returned_request)

    def test_get_request_from_setup_where_request_not_found(self):
        """
        (edge case) This will probably never happen, but if the
        first argument of View.setup is not an HttpRequest object,
        then raise an exception.
        """

        # Arrange
        cbv_instance = create_autospec(views.HelloTest)
        cbv_method = MagicMock()
        cbv_method.__name__ = "setup"

        # Act/Assert
        with self.assertRaises(DjCbvException):
            get_request(cbv_instance, cbv_method, Mock())

    def test_get_request_from_instance(self):
        """
        Test retrieving request from view instance, i.e. `self.request`.
        """

        # Arrange
        request = RequestFactory().get("/")
        cbv_instance = create_autospec(views.HelloTest)
        cbv_instance.request = request
        cbv_method = MagicMock()
        cbv_method.__name__ = "dispatch"

        # Act
        returned_request = get_request(cbv_instance, cbv_method)

        # Assert
        self.assertEqual(request, returned_request)

    def test_get_request_returns_none_if_request_not_found(self):
        """
        Test that None is returned if the request cannot be found
        on the view instance or view method.
        """

        # Arrange
        cbv_instance = create_autospec(views.HelloTest)
        cbv_method = MagicMock()
        cbv_method.__name__ = "some_method"

        # Act
        returned_request = get_request(cbv_instance, cbv_method)

        # Assert
        self.assertIsNone(returned_request)


class TestSetLogParents(unittest.TestCase):
    """
    Tests for the `set_log_parents` util function.
    """

    def setUp(self):
        self.request = MagicMock()
        self.request._djcbv_inspect_metadata.logs = {}

    def test_initial_log(self):
        """
        Test that the first log has no parents and is not a parent.

        log (1) <--- current log
        """

        # Arrange
        first_log = DjCbvLog(order=1, indent=0)
        self.request._djcbv_inspect_metadata.logs[1] = first_log

        # Act
        set_log_parents(1, self.request)

        # Assert
        self.assertFalse(first_log.is_parent)
        self.assertTrue(len(first_log.parent_list) == 0)

    def test_log_with_no_parent(self):
        """
        Test log that has no parents (the prior log has same indent log).

        log (1)
        log (2) <--- current log
        """

        # Arrange
        log_1 = DjCbvLog(order=1, indent=0)
        current_log_order = 2
        current_log = DjCbvLog(order=current_log_order, indent=0)
        self.request._djcbv_inspect_metadata.logs[1] = log_1
        self.request._djcbv_inspect_metadata.logs[2] = current_log

        # Act
        set_log_parents(current_log_order, self.request)

        # Assert
        self.assertFalse(current_log.is_parent)
        self.assertTrue(len(current_log.parent_list) == 0)

    def test_log_with_nested_parents(self):
        """
        Test log that has multiple parents.

        log (1)
        ....log (2)
        ........log (3) <--- current log
        """

        # Arrange
        log_1 = DjCbvLog(order=1, indent=0, is_parent=True)
        log_2 = DjCbvLog(order=2, indent=1, parent_list=["cbvInspect_1_0"])
        current_log_order = 3
        current_log = DjCbvLog(order=current_log_order, indent=2)
        self.request._djcbv_inspect_metadata.logs[1] = log_1
        self.request._djcbv_inspect_metadata.logs[2] = log_2
        self.request._djcbv_inspect_metadata.logs[3] = current_log

        # Act
        set_log_parents(current_log_order, self.request)

        # Assert
        self.assertFalse(current_log.is_parent)
        self.assertTrue(log_2.is_parent)
        self.assertEqual(current_log.parent_list, ["cbvInspect_1_0", "cbvInspect_2_1"])

    def test_log_with_ancestor_parent(self):
        """
        Test log that doesn't have a direct parent.

        log (1)
        ....log (2)
        ........log (3)
        ....log (4) <--- current log
        """

        # Arrange
        log_1 = DjCbvLog(order=1, indent=0, is_parent=True)
        log_2 = DjCbvLog(order=2, indent=1, is_parent=True, parent_list=["cbvInspect_1_0"])
        log_3 = DjCbvLog(order=3, indent=2, parent_list=["cbvInspect_1_0", "cbvInspect_2_1"])
        current_log_order = 4
        current_log = DjCbvLog(order=current_log_order, indent=1)
        self.request._djcbv_inspect_metadata.logs[1] = log_1
        self.request._djcbv_inspect_metadata.logs[2] = log_2
        self.request._djcbv_inspect_metadata.logs[3] = log_3
        self.request._djcbv_inspect_metadata.logs[4] = current_log

        # Act
        set_log_parents(current_log_order, self.request)

        # Assert
        self.assertFalse(current_log.is_parent)
        self.assertFalse(log_3.is_parent)
        self.assertEqual(current_log.parent_list, ["cbvInspect_1_0"])
