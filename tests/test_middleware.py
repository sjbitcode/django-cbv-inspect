from unittest.mock import patch, MagicMock, create_autospec

from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import resolve

from django_cbv_inspect.middleware import DjCbvInspectMiddleware
from django_cbv_inspect.mixins import DjCbvInspectMixin


class TestDjCBVInspectMiddleware(TestCase):
    def setUp(self):
        self.mock_get_response = MagicMock()
        self.middleware = DjCbvInspectMiddleware(self.mock_get_response)
        self.request = RequestFactory().get('/simple_cbv_render')

    def test_client_request_for_cbv(self):
        """
        Test the end-to-end request/response for a class-based view.

        Assert that the djCbv markup is in the response content and the
        middleware cleaned up the mixin class from the original request.
        """
        # Arrange
        client = Client()

        # Act
        response = client.get('/simple_cbv_render')

        # Assert
        self.assertTrue('id="djCbv"' in response.content.decode(response.charset))
        bases = resolve(response._request.path).func.view_class.__bases__
        self.assertTrue(DjCbvInspectMixin not in bases)

    def test_client_request_for_fbv(self):
        """
        Test the end-to-end request/response for a function-based view.
        Assert that djCbv markup is in the response content, but shows
        appropriate data for fbv.
        """
        # Arrange
        client = Client()

        # Act
        response = client.get('/simple_fbv_render')

        # Assert
        self.assertTrue('id="djCbv"' in response.content.decode(response.charset))
        self.assertTrue('No CBV method call chain' in response.content.decode(response.charset))

    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', return_value=False)
    def test_middleware_returns_response_if_response_not_insertable(self, _, __):
        """
        Test that the middleware does not append djCbv markup
        to a non-html response by checking that the get_response content
        is same as the response after middleware finishes.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        response.content = b'foo'
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res.content.decode(), 'foo')

    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_returns_response_for_malformed_html(self, _, __):
        """
        Test that the middleware does not append djCbv markup
        to a malformed html response by checking that the get_response content
        is same as the response after middleware finishes.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.content = bytes('<foo>', response.charset)
        response.__contains__.return_value = True  # "Content-Length" in response
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res.content.decode(res.charset), '<foo>')

    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_inserts_toolbar_html_if_content_length_set(self, _, __):
        """
        Test that the middleware appends djCbv markup and updates the
        Content-Length header.
        """
        # Arrange
        html_content = '<html><head></head><body><p>test</p></body></html>'
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.headers = {"Content-Length": len(html_content)}
        response.__contains__.side_effect = response.headers.__contains__  # "Content-Length" in response
        response.__setitem__.side_effect = response.headers.__setitem__  # response["Content-Length"] = 100
        response.__getitem__.side_effect = response.headers.__getitem__  # response["Content-Length"]
        response.content = bytes(html_content, response.charset)
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)
        self.assertTrue(res['Content-Length'] > len(html_content))

    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin')
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', return_value=True)
    def test_middleware_inserts_toolbar_html_even_if_content_length_not_set(self, _, __):
        """
        Test that the middleware appends djCbv markup even if the response
        does not have a Content-Length header.
        """
        # Arrange
        html_content = '<html><head></head><body><p>test</p></body></html>'
        response = create_autospec(HttpResponse)
        response.charset = 'utf-8'
        response.content = bytes(html_content, response.charset)
        response.__contains__.return_value = False  # "Content-Length" in response
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)
