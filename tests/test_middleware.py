from unittest.mock import patch, MagicMock, create_autospec

from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import resolve

from django_cbv_inspect.middleware import DjCbvInspectMiddleware
from django_cbv_inspect.mixins import DjCbvInspectMixin


class TestDjCBVInspectMiddleware(TestCase):
    def setUp(self):
        self.mock_get_response = MagicMock()
        self.middleware = DjCbvInspectMiddleware(self.mock_get_response)
        self.request = RequestFactory().get('/simple_cbv_render')

        self.patch_show_toolbar = patch.object(DjCbvInspectMiddleware, 'show_toolbar', return_value=True)
        self.mock_show_toolbar = self.patch_show_toolbar.start()

        self.addCleanup(patch.stopall)

    @patch('django_cbv_inspect.middleware.DjCbvToolbar.__init__')
    @patch('django_cbv_inspect.middleware.DjCbvInspectMiddleware._add_djcbv_mixin')
    def test_client_request_for_cbv_returns_early_when_show_toolbar_false(self, mock_add_mixin, mock_toolbar_init):
        """
        Test the end-to-end request/response for a class-based view when the toolbar should not run.

        Test that the middleware's process_view does not run and exits early.
        Note: Check to show toolbar happens in two places in the middleware:
            1. __call__ method
            2. process_view method(this gets called on all get_response calls)
        """
        # Arrange
        self.mock_show_toolbar.return_value = False
        client = Client()

        # Act
        response = client.get('/simple_cbv_render')

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))
        mock_toolbar_init.assert_not_called()
        mock_add_mixin.assert_not_called()

    @override_settings(DEBUG=False)
    def test_middleware_show_toolbar_check_reads_from_settings(self):
        """
        Test that the show_toolbar method determines value based on settings.DEBUG.

        Override DEBUG settings to False and check that the show_toolbar() returns False.
        """
        # Arrange
        self.patch_show_toolbar.stop()  # temporarily stop this mock!

        # Act
        should_show_toolbar = self.middleware.show_toolbar()

        self.patch_show_toolbar.start()  # start this mock again!

        # Assert
        self.assertFalse(should_show_toolbar)

    def test_client_request_for_cbv_happy_path(self):
        """
        Test the end-to-end request/response for a class-based view when the toolbar should run.

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
        to a non-html response by checking that the get_response() content
        is same as the content of the response returned by the middleware.
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
        to a malformed html response by checking that the get_response() content
        is same as the content of the response returned by the middleware.
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
