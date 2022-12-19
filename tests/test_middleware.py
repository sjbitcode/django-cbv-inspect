from unittest.mock import patch, MagicMock, create_autospec

from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import resolve

from django_cbv_inspect.middleware import DjCBVInspectMiddleware
from django_cbv_inspect.mixins import DjCBVInspectMixin


class TestDjCBVInspectMiddleware(TestCase):
    def setUp(self):
        self.mock_get_response = MagicMock()
        self.middleware = DjCBVInspectMiddleware(self.mock_get_response)
        self.request = RequestFactory().get('/simple_cbv_render')

    def test_client_request_for_cbv(self):
        # Arrange
        client = Client()

        # Act
        response = client.get('/simple_cbv_render')

        # Assert
        self.assertTrue('id="djCbv"' in response.content.decode(response.charset))
        bases = resolve(response._request.path).func.view_class.__bases__
        self.assertTrue(DjCBVInspectMixin not in bases)

    def test_client_request_for_fbv(self):
        # Arrange
        client = Client()

        # Act
        response = client.get('/simple_fbv_render')

        # Assert
        self.assertTrue('id="djCbv"' in response.content.decode(response.charset))
        self.assertTrue('No CBV method call chain' in response.content.decode(response.charset))

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCBVInspectMiddleware, '_is_response_insertable', return_value=False)
    def test_middleware_returns_response_if_response_not_insertable(self, _, __):
        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res, response)

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCBVInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_returns_response_for_malformed_html(self, _, __):
        # Arrange
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.content = bytes('<foo>', response.charset)
        response.__contains__.return_value = True  # to pass "Content-Length" in response check
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res, response)

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCBVInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_inserts_toolbar_html_if_content_length_set(self, _, __):
        # Arrange
        html_content = '<html><head></head><body><p>test</p></body></html>'
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.content = bytes(html_content, response.charset)
        response.__contains__.return_value = True  # to explicitly pass "Content-Length" in response check
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCBVInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_inserts_toolbar_html_even_if_content_length_not_set(self, _, __):
        # Arrange
        html_content = '<html><head></head><body><p>test</p></body></html>'
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.content = bytes(html_content, response.charset)
        response.__contains__.return_value = False  # to explicitly fail "Content-Length" in response check
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    def test_middleware__is_response_insertable_returns_true(self, _):
        # Arrange
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.streaming = False
        response.content = bytes("", response.charset)
        response_values = {"Content-Type": "text/html; charset=utf-8"}
        response.get.side_effect = response_values.get

        # Act
        is_insertable = self.middleware._is_response_insertable(response)

        # Assert
        self.assertTrue(is_insertable)

    @patch.object(DjCBVInspectMiddleware, '_remove_djcbv_mixin')
    def test_middleware__is_response_insertable_returns_false(self, _):
        # Arrange
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.streaming = False
        response.content = bytes('{"foo": "bar"}', response.charset)
        response_values = {"Content-Type": "application/json"}
        response.get.side_effect = response_values.get

        # Act
        is_insertable = self.middleware._is_response_insertable(response)

        # Assert
        self.assertFalse(is_insertable)
