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

        self.addCleanup(patch.stopall)

    @override_settings(DEBUG=False)
    def test_middleware_show_toolbar_check_reads_from_settings(self):
        """
        Test that the `show_toolbar` method determines value based on settings.DEBUG.
        """
        # Act
        should_show_toolbar = self.middleware.show_toolbar()

        # Assert
        self.assertFalse(should_show_toolbar)

    @patch('django_cbv_inspect.middleware.resolve')
    def test_middleware_view_excludes_check_returns_true_when_attr_exists(self, mock_resolve):
        """
        Test that the `is_view_excluded` method returns True when
        the `djcbv_exclude` attr exists on the view function.
        """
        # Arrange
        mock_resolve.return_value.func = MagicMock(djcbv_exclude=True)

        # Act
        is_excluded = self.middleware.is_view_excluded(self.request)

        # Assert
        self.assertTrue(is_excluded)

    @patch('django_cbv_inspect.middleware.resolve')
    def test_middleware_view_excludes_check_returns_false_when_attr_does_not_exist(self, mock_resolve):
        """
        Test that the `is_view_excluded` method returns False when
        the `djcbv_exclude` attr is missing from the view function.
        """
        # Arrange
        mock_view_func = MagicMock()
        del mock_view_func.djcbv_exclude
        mock_resolve.return_value.func = mock_view_func

        # Act
        is_excluded = self.middleware.is_view_excluded(self.request)

        # Assert
        self.assertFalse(is_excluded)

    @patch('django_cbv_inspect.utils.is_cbv_request', new=MagicMock(return_value=False))
    @patch('django_cbv_inspect.middleware.DjCbvToolbar.__init__', return_value=None)
    def test_middleware_does_not_process_request_for_non_cbv_request(self, mock_toolbar_init):
        """
        Test that the `should_process_request` method returns False and the middleware exits early
        when the request maps to a function-based view.

        As a result, the DjCbvToolbar class should not be instantiated.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_not_called()

    @patch.object(DjCbvInspectMiddleware, 'show_toolbar', new=MagicMock(return_value=False))
    @patch('django_cbv_inspect.utils.is_cbv_request', new=MagicMock(return_value=True))
    @patch('django_cbv_inspect.middleware.DjCbvToolbar.__init__', return_value=None)
    def test_middleware_does_not_process_request_when_show_toolbar_is_false(self, mock_toolbar_init):
        """
        Test that the `should_process_request` method returns False and the middleware exits early
        when `show_toolbar` is False.

        As a result, the DjCbvToolbar class should not be instantiated.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_not_called()

    @patch.object(DjCbvInspectMiddleware, 'show_toolbar', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, 'is_view_excluded', new=MagicMock(return_value=True))
    @patch('django_cbv_inspect.utils.is_cbv_request', new=MagicMock(return_value=True))
    @patch('django_cbv_inspect.middleware.DjCbvToolbar.__init__', return_value=None)
    def test_middleware_does_not_process_request_when_view_is_excluded(self, mock_toolbar_init):
        """
        Test that the `should_process_request` method returns False and the middleware exits early
        when the request for a class-based view is excluded.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_not_called()

    @patch.object(DjCbvInspectMiddleware, 'show_toolbar', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, 'is_view_excluded', new=MagicMock(return_value=False))
    @patch('django_cbv_inspect.utils.is_cbv_request', new=MagicMock(return_value=True))
    @patch('django_cbv_inspect.middleware.DjCbvToolbar.__init__', return_value=None)
    def test_middleware_should_process_request_for_nonexcluded_cbv_views_when_show_toolbar_true(self, mock_toolbar_init):
        """
        Test that the `should_process_request` method returns True and middleware runs
        when the request for a class-based view is not excluded and `show_toolbar` is True.
        """
        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_called_once()

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin', new=MagicMock())
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', new=MagicMock(return_value=False))
    def test_middleware_returns_response_if_response_not_insertable(self):
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

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin', new=MagicMock())
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', new=MagicMock(return_value=True))
    def test_middleware_returns_response_for_malformed_html(self):
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

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin', new=MagicMock())
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', new=MagicMock(return_value=True))
    def test_middleware_inserts_toolbar_html_if_content_length_set(self):
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

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, '_remove_djcbv_mixin', new=MagicMock())
    @patch.object(DjCbvInspectMiddleware, '_is_response_insertable', new=MagicMock(return_value=True))
    def test_middleware_inserts_toolbar_html_even_if_content_length_not_set(self):
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

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, '_add_djcbv_mixin')
    def test_middleware_process_view_runs_when_process_request_is_true(self, mock_add_mixin):
        """
        Test that the middleware `process_view` hook runs when `should_process_request`
        is True.

        Even if the middleware exits early in `__call__`, the `get_response` calls which
        still triggers the `process_view` hook, hence the secondary check here.
        """
        # Act
        self.middleware.process_view(self.request, MagicMock(), (), {})

        # Assert
        mock_add_mixin.assert_called_once()

    @patch.object(DjCbvInspectMiddleware, 'should_process_request', new=MagicMock(return_value=False))
    @patch.object(DjCbvInspectMiddleware, '_add_djcbv_mixin')
    def test_middleware_process_view_does_not_run_when_process_request_is_false(self, mock_add_mixin):
        """
        Test that the middleware `process_view` hook exits early when `should_process_request`
        is False.

        Even if the middleware exits early in `__call__`, the `get_response` calls which
        still triggers the `process_view` hook, hence the secondary check here.
        """
        # Act
        self.middleware.process_view(self.request, MagicMock(), (), {})

        # Assert
        mock_add_mixin.assert_not_called()


@override_settings(DEBUG=True)
class TestMiddlewareWithClient(TestCase):
    def test_client_request_for_fbv_returns_early(self):
        """
        Test the end-to-end request/response for a function-based view.

        Assert that the toolbar is not shown.
        """
        # Arrange
        client = Client()

        # Act
        response = client.get('/simple_fbv_render')

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_returns_early_when_excluded_with_mixin(self):
        """
        Test the end-to-end request/response for an excluded class-based view using the mixin.

        Assert that the toolbar is not shown.
        """
        # Arrange
        client = Client()

        # Act
        response = client.get('/djcbv_exclude_mixin')

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_returns_early_when_excluded_with_decorator(self):
        """
        Test the end-to-end request/response for an excluded class-based view
        using the method decorator.

        Assert that the toolbar is not shown.
        """
        # Arrange
        client = Client()

        # Act
        response = client.get('/djcbv_exclude_dec')

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_shows_toolbar(self):
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
