import unittest
# from unittest.mock import patch

from django import get_version
from django.http import HttpRequest, HttpResponse
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
    get_cls_from_method,
    cls_has_method,
    get_sourcecode,
    get_super_calls,
    get_request
)
from . import test_helpers, views


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


class TestGetCCBVLink(unittest.TestCase):
    @staticmethod
    def ping_ccbv_url(ccbv_url):
        response = requests.get(ccbv_url)
        return response.status_code

    def test_ccbv_link_returns_link_for_CBV_cls(self):
        # Arrange
        version: str = get_version().rsplit(".", 1)[0]
        module: str = TemplateView.__module__
        expected_ccbv_url = f"https://ccbv.co.uk/projects/Django/{version}/{module}/{TemplateView.__name__}"

        # Act
        ccbv_url = get_ccbv_link(TemplateView)

        # Assert
        self.assertEqual(expected_ccbv_url, ccbv_url)
        # self.assertTrue(self.ping_ccbv_url(ccbv_url), 200)

    def test_ccbv_link_returns_link_for_CBV_method(self):
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
        # self.assertTrue(self.ping_ccbv_url(ccbv_url), 200)

    def test_ccbv_link_does_not_return_link_for_non_CBV_cls(self):
        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView))

    def test_ccbv_link_does_not_return_link_for_non_CBV_method(self):
        # Act/Assert
        self.assertIsNone(get_ccbv_link(views.RenderHtmlView.get_context_data))
