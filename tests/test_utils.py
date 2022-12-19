from collections import namedtuple
import inspect
import unittest
from unittest.mock import patch, Mock, MagicMock, create_autospec

from django import get_version
from django.test import RequestFactory, TestCase
from django.views.generic import TemplateView
import requests

from django_cbv_inspect.utils import (
    DjCBVClassOrMethodInfo,
    is_view_cbv,
    collect_parent_classes,
    get_bases,
    get_mro,
    get_ccbv_link,
    get_path,
    serialize_params,
    mask_request,
    mask_queryset,
    get_class_from_method,
    class_has_method,
    get_sourcecode,
    get_super_calls,
    get_request
)
from django_cbv_inspect.mixins import DjCBVInspectMixin
from . import test_helpers, views, models


class TestIsViewCbv(unittest.TestCase):

    def test_is_view_cbv_returns_true_for_cbv_func(self):
        # Arrange
        view_func = views.RenderHtmlView.as_view()

        # Act
        from_cbv = is_view_cbv(view_func)

        # Assert
        self.assertTrue(from_cbv)

    def test_is_view_cbv_returns_false_for_fbv(self):
        # Arrange
        view_func = views.fbv_render

        # Act
        from_cbv = is_view_cbv(view_func)

        # Assert
        self.assertFalse(from_cbv)


class TestCollectParentClasses(unittest.TestCase):

    def test_collect_parent_classes_returns_metadata_for_mro(self):
        # Arrange
        mro = test_helpers.FuturisticFoo.__mro__
        mro_cls_metadata = []

        for mro_cls in mro:
            mro_cls_metadata.append(DjCBVClassOrMethodInfo(
                ccbv_link=None,
                name=f"{mro_cls.__module__}.{mro_cls.__name__}",
                signature=None
            ))

        # Act
        cls_metadata = collect_parent_classes(test_helpers.FuturisticFoo, "__mro__")
        cls_metadata_from_mro = get_mro(test_helpers.FuturisticFoo)

        # Assert
        self.assertEqual(mro_cls_metadata, cls_metadata)
        self.assertEqual(mro_cls_metadata, cls_metadata_from_mro)

    def test_collect_parent_classes_returns_metadata_for_bases(self):
        # Arrange
        bases = test_helpers.FuturisticFoo.__bases__
        base_cls_metadata = []

        for base_cls in bases:
            base_cls_metadata.append(DjCBVClassOrMethodInfo(
                ccbv_link=None,
                name=f"{base_cls.__module__}.{base_cls.__name__}",
                signature=None
            ))

        # Act
        cls_metadata = collect_parent_classes(test_helpers.FuturisticFoo, "__bases__")
        cls_metadata_from_get_bases = get_bases(test_helpers.FuturisticFoo)

        # Assert
        self.assertEqual(base_cls_metadata, cls_metadata)
        self.assertEqual(base_cls_metadata, cls_metadata_from_get_bases)

    def test_collect_parent_classes_skips_djcbvinspectmixin(self):
        # Arrange
        bases = test_helpers.DjFoo.__bases__
        base_cls_metadata = []

        for base_cls in bases:
            if base_cls is not DjCBVInspectMixin:
                base_cls_metadata.append(DjCBVClassOrMethodInfo(
                    ccbv_link=None,
                    name=f"{base_cls.__module__}.{base_cls.__name__}",
                    signature=None
                ))

        # Act
        cls_metadata = collect_parent_classes(test_helpers.DjFoo, "__bases__")
        cls_metadata_from_get_bases = get_bases(test_helpers.DjFoo)

        # Assert
        self.assertEqual(base_cls_metadata, cls_metadata)
        self.assertEqual(base_cls_metadata, cls_metadata_from_get_bases)


class TestGetCCBVLink(unittest.TestCase):
    @staticmethod
    def ping_ccbv_url(ccbv_url):
        response = requests.get(ccbv_url)
        return response.status_code

    def test_ccbv_link_returns_link_for_cbv_cls(self):
        # Arrange
        version: str = get_version().rsplit(".", 1)[0]
        module: str = TemplateView.__module__
        expected_ccbv_url = f"https://ccbv.co.uk/projects/Django/{version}/{module}/{TemplateView.__name__}"

        # Act
        ccbv_url = get_ccbv_link(TemplateView)

        # Assert
        self.assertEqual(expected_ccbv_url, ccbv_url)

    def test_ccbv_link_returns_link_for_cbv_method(self):
        # Arrange
        cbv_method = TemplateView.get_template_names

        version: str = get_version().rsplit(".", 1)[0]
        module: str = TemplateView.__module__
        class_name, method_name = cbv_method.__qualname__.rsplit(".", 1)
        expected_ccbv_url = f"https://ccbv.co.uk/projects/Django/{version}/{module}/{class_name}/#{method_name}"

        # Act
        ccbv_url = get_ccbv_link(cbv_method)

        # Assert
        self.assertEqual(expected_ccbv_url, ccbv_url)

    @patch.object(inspect, 'isclass', return_value=False)
    def test_ccbv_link_does_not_return_link_for_cbv_nonclass(self, _):
        # Arrange
        mock_obj = Mock()
        mock_obj.__module__ = TemplateView.__module__

        # Act
        ccbv_url = get_ccbv_link(mock_obj)

        # Assert
        self.assertEqual(None, ccbv_url)

    def test_ccbv_link_does_not_return_link_for_non_cbv_cls(self):
        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView))

    def test_ccbv_link_does_not_return_link_for_non_cbv_method(self):
        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView.get_context_data))


@patch.object(inspect, "getfile")
class TestGetPath(unittest.TestCase):
    def test_get_path_for_dependency_returns_truncated_path(self, mock_getfile):
        # Arrange
        mock_getfile.return_value = "some/path/site-packages/cool/cool_class.py"
        expected_return_path = "/cool/cool_class.py"

        # Act
        path = get_path(Mock())

        # Assert
        self.assertEqual(expected_return_path, path)

    def test_get_path_for_internal_dependency_returns_full_path(self, mock_getfile):
        # Arrange
        mock_getfile.return_value = "some/path/cool/cool_class.py"

        # Act
        path = get_path(Mock())

        # Assert
        self.assertEqual(mock_getfile.return_value, path)


class TestSerializeParams(unittest.TestCase):
    @patch("django_cbv_inspect.utils.mask_request")
    @patch("django_cbv_inspect.utils.mask_queryset")
    @patch("django_cbv_inspect.utils.pformat")
    def test_serialize_params_calls_pformat_and_clean_functions(
        self, mock_pformat, mock_mask_queryset, mock_mask_req
    ):
        # Act
        serialize_params({"name": "Foo"})

        # Assert
        mock_pformat.assert_called_once()
        mock_mask_req.assert_called_once()
        mock_mask_queryset.assert_called_once()


class TestMaskRequest(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_mask_request_replaces_string_correctly(self):
        # Arrange
        SubTestArgs = namedtuple("SubTestArgs", "passed expected")
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
    def setUp(self):
        self.model = models.Book
        self.model.objects.create(name="The Witches")
        self.model.objects.create(name="Harry Potter and the Chamber of Apps")

    def test_mask_queryset_replaces_string_correctly(self):
        # Arrange
        SubTestArgs = namedtuple("SubTestArgs", "passed expected")
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


class TestGetClassFromMethod(unittest.TestCase):
    def test_get_class_from_method_returns_class_object(self):
        """
        This tests a method on a class that is not defined on the parent class.
        """
        # Arrange
        foo_cls = test_helpers.Foo

        # Act
        cls = get_class_from_method(foo_cls.goodbye)

        # Assert
        self.assertEqual(cls, foo_cls)

    def test_get_class_from_overriden_method_returns_class_object(self):
        """
        This tests a method on a class that is overriden.
        """
        # Arrange
        foo_cls = test_helpers.Foo

        # Act
        cls = get_class_from_method(foo_cls.greet)  # Foo's superclass also defines greet

        # Assert
        self.assertEqual(cls, foo_cls)


class TestClassHasMethod(unittest.TestCase):
    def test_class_has_method_returns_true_for_method(self):
        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.Foo, "greet"))

    def test_class_has_method_returns_false_for_attribue(self):
        # Act/Assert
        self.assertFalse(class_has_method(test_helpers.Foo, "color"))

    def test_class_has_method_returns_false_for_nonexistent_method(self):
        # Act/Assert
        self.assertFalse(class_has_method(test_helpers.Foo, "some_method"))

    def test_class_has_method_returns_true_for_inherited_method(self):
        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "greet"))

    def test_class_has_method_returns_true_for_classmethod(self):
        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "get_cls_color"))

    def test_class_has_method_returns_true_for_staticmethod(self):
        # Act/Assert
        self.assertTrue(class_has_method(test_helpers.FuturisticFoo, "get_number"))


class TestGetSourcecode(unittest.TestCase):
    def test_get_sourcecode_strips_docstring(self):
        # Act
        sourcecode = get_sourcecode(test_helpers.sample_func)

        # Assert
        self.assertFalse("Sample docstring" in sourcecode)
        self.assertFalse("comment" in sourcecode)
        self.assertFalse("#" in sourcecode)

    def test_get_sourcecode_for_func_witout_docstring_or_comments(self):
        # Act
        sourcecode = get_sourcecode(test_helpers.sample_func2)

        # Assert
        self.assertFalse("#" in sourcecode)
        self.assertEqual(sourcecode, inspect.getsource(test_helpers.sample_func2))


class TestGetSuperCalls(unittest.TestCase):
    def test_method_with_no_super_returns_none(self):
        # Act
        super_calls = get_super_calls(test_helpers.Foo, test_helpers.Foo.goodbye)

        # Assert
        self.assertIsNone(super_calls)

    def test_super_call_that_resolves_to_direct_parent(self):
        """
        This test runs for the Foo and Foo.greet.
        Foo.greet has a super call that resolves to one of its base classes, AncientFoo.
        """
        # Arrange
        expected_super_call = DjCBVClassOrMethodInfo(
            ccbv_link=None,
            name=test_helpers.AncientFoo.greet.__qualname__,
            signature=str(inspect.signature(test_helpers.AncientFoo.greet))
        )

        # Act
        super_calls = get_super_calls(test_helpers.Foo, test_helpers.Foo.greet)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_that_resolves_to_ancestor(self):
        """
        This test runs for FuturisticFoo and FuturisticFoo.customize_greet.
        FuturisticFoo.customize_greet has a super call that resolves to one of its mro classes, AncientFoo.
        """
        # Arrange
        expected_super_call = DjCBVClassOrMethodInfo(
            ccbv_link=None,
            name=test_helpers.AncientFoo.customize_greet.__qualname__,
            signature=str(inspect.signature(test_helpers.AncientFoo.customize_greet))
        )

        # Act
        super_calls = get_super_calls(test_helpers.FuturisticFoo, test_helpers.FuturisticFoo.customize_greet)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_that_does_not_resolve(self):
        # Arrange
        expected_super_call = {}

        # Act
        super_calls = get_super_calls(test_helpers.FuturisticFoo, test_helpers.FuturisticFoo.test)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])

    def test_super_call_for_different_method_than_calling_method(self):
        # Arrange
        expected_super_call = DjCBVClassOrMethodInfo(
            ccbv_link=None,
            name=test_helpers.AncientFoo.greet_in_spanish.__qualname__,
            signature=str(inspect.signature(test_helpers.AncientFoo.greet_in_spanish))
        )

        # Act
        super_calls = get_super_calls(test_helpers.FuturisticFoo, test_helpers.FuturisticFoo.excited_spanish_greet)

        # Assert
        self.assertEqual(1, len(super_calls))
        self.assertEqual(expected_super_call, super_calls[0])


class TestGetRequest(unittest.TestCase):
    def test_get_request_from_setup(self):
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
        This will probably never happen, but if the first arg of setup is not
        an HttpRequest object, then raise exception.
        """
        # Arrange
        cbv_instance = create_autospec(views.HelloTest)
        cbv_method = MagicMock()
        cbv_method.__name__ = "setup"

        # Act/Assert
        with self.assertRaises(Exception):
            get_request(cbv_instance, cbv_method, Mock())

    def test_get_request_from_instance(self):
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

    def test_get_request_raises_exception_if_request_not_found(self):
        # Arrange
        cbv_instance = create_autospec(views.HelloTest)
        cbv_method = MagicMock()
        cbv_method.__name__ = "some_method"

        # Act/Assert
        with self.assertRaises(Exception):
            get_request(cbv_instance, cbv_method)
