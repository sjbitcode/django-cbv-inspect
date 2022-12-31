from unittest.mock import MagicMock, create_autospec, patch

from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import resolve

from cbv_inspect.middleware import DjCbvInspectMiddleware
from cbv_inspect.mixins import DjCbvInspectMixin


class TestDjCBVInspectMiddleware(TestCase):
    """
    Tests for the `DjCbvInspectMiddleware` middleware class.
    """

    def setUp(self):
        self.mock_get_response = MagicMock()
        self.middleware = DjCbvInspectMiddleware(self.mock_get_response)
        self.request = RequestFactory().get("/simple_cbv_render")

        self.addCleanup(patch.stopall)

    @override_settings(DEBUG=False)
    def test_show_toolbar_reads_from_settings(self):
        """
        Test that the `show_toolbar` method determines value based on settings.DEBUG.
        """

        # Act
        should_show_toolbar = self.middleware.show_toolbar()

        # Assert
        self.assertFalse(should_show_toolbar)

    @patch("cbv_inspect.middleware.resolve")
    def test_view_excluded_check_is_true_when_attr_exists(self, mock_resolve):
        """
        Test that the `is_view_excluded` method determines a view
        is excluded if the `djcbv_exclude` attr exists on the view function.
        """

        # Arrange
        mock_resolve.return_value.func = MagicMock(djcbv_exclude=True)

        # Act
        is_excluded = self.middleware.is_view_excluded(self.request)

        # Assert
        self.assertTrue(is_excluded)

    @patch("cbv_inspect.middleware.resolve")
    def test_view_excluded_check_is_false_when_attr_does_not_exist(self, mock_resolve):
        """
        Test that the `is_view_excluded` method determines a view is not excluded
        if the `djcbv_exclude` attr is not present on the view function.
        """

        # Arrange
        mock_view_func = MagicMock()
        del mock_view_func.djcbv_exclude
        mock_resolve.return_value.func = mock_view_func

        # Act
        is_excluded = self.middleware.is_view_excluded(self.request)

        # Assert
        self.assertFalse(is_excluded)

    @patch("cbv_inspect.utils.is_cbv_request", new=MagicMock(return_value=False))
    @patch("cbv_inspect.middleware.DjCbvToolbar.__init__", return_value=None)
    def test_middleware_does_not_process_request_for_fbv_request(self, mock_toolbar_init):
        """
        Test that the `should_process_request` makes the middleware exit early
        for a function-based view.

        As a result, the DjCbvToolbar class should not be instantiated.
        """

        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_not_called()

    @patch.object(DjCbvInspectMiddleware, "show_toolbar", new=MagicMock(return_value=False))
    @patch("cbv_inspect.utils.is_cbv_request", new=MagicMock(return_value=True))
    @patch("cbv_inspect.middleware.DjCbvToolbar.__init__", return_value=None)
    def test_middleware_does_not_process_request_when_show_toolbar_is_false(
        self, mock_toolbar_init
    ):
        """
        Test that the `should_process_request` makes the middleware exit early
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

    @patch.object(DjCbvInspectMiddleware, "show_toolbar", new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, "is_view_excluded", new=MagicMock(return_value=True))
    @patch("cbv_inspect.utils.is_cbv_request", new=MagicMock(return_value=True))
    @patch("cbv_inspect.middleware.DjCbvToolbar.__init__", return_value=None)
    def test_middleware_does_not_process_request_when_view_is_excluded(self, mock_toolbar_init):
        """
        Test that the `should_process_request` makes the middleware exit early
        when a view is excluded.
        """

        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_not_called()

    @patch.object(DjCbvInspectMiddleware, "show_toolbar", new=MagicMock(return_value=True))
    @patch.object(DjCbvInspectMiddleware, "is_view_excluded", new=MagicMock(return_value=False))
    @patch("cbv_inspect.utils.is_cbv_request", new=MagicMock(return_value=True))
    @patch("cbv_inspect.middleware.DjCbvToolbar.__init__", return_value=None)
    def test_middleware_should_process_request_allows_cbv_view(self, mock_toolbar_init):
        """
        Test that the `should_process_request` allows middleware to run fully.
        """

        # Arrange
        response = create_autospec(HttpResponse)
        self.mock_get_response.return_value = response

        # Act
        self.middleware(self.request)

        # Assert
        mock_toolbar_init.assert_called_once()

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=True)
    )
    @patch.object(DjCbvInspectMiddleware, "_remove_djcbv_mixin", new=MagicMock())
    @patch.object(
        DjCbvInspectMiddleware, "_is_response_insertable", new=MagicMock(return_value=False)
    )
    def test_middleware_exits_if_response_not_insertable(self):
        """
        Test that the middleware does not append djCbv markup to
        a non-html response.
        """

        # Arrange
        response = create_autospec(HttpResponse)
        response.content = b"foo"
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res.content.decode(), "foo")

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=True)
    )
    @patch.object(DjCbvInspectMiddleware, "_remove_djcbv_mixin", new=MagicMock())
    @patch.object(
        DjCbvInspectMiddleware, "_is_response_insertable", new=MagicMock(return_value=True)
    )
    def test_middleware_exits_for_malformed_html_response(self):
        """
        Test that the middleware does not append djCbv markup to
        a malformed html response.
        """

        # Arrange
        response = create_autospec(HttpResponse)
        response.charset = "utf-8"
        response.content = bytes("<foo>", response.charset)
        response.__contains__.return_value = True  # "Content-Length" in response
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertEqual(res.content.decode(res.charset), "<foo>")

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=True)
    )
    @patch.object(DjCbvInspectMiddleware, "_remove_djcbv_mixin", new=MagicMock())
    @patch.object(
        DjCbvInspectMiddleware, "_is_response_insertable", new=MagicMock(return_value=True)
    )
    def test_middleware_updates_content_length_header_if_exists(self):
        """
        Test that the middleware appends djCbv markup and updates the
        Content-Length header if it exists.
        """

        # Arrange
        html_content = "<html><head></head><body><p>test</p></body></html>"
        response = create_autospec(HttpResponse)
        response.charset = "utf-8"
        response.headers = {"Content-Length": len(html_content)}
        response.__contains__.side_effect = (
            response.headers.__contains__
        )  # "Content-Length" in response
        response.__setitem__.side_effect = (
            response.headers.__setitem__
        )  # response["Content-Length"] = 100
        response.__getitem__.side_effect = (
            response.headers.__getitem__
        )  # response["Content-Length"]
        response.content = bytes(html_content, response.charset)
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)
        self.assertTrue(res["Content-Length"] > len(html_content))

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=True)
    )
    @patch.object(DjCbvInspectMiddleware, "_remove_djcbv_mixin", new=MagicMock())
    @patch.object(
        DjCbvInspectMiddleware, "_is_response_insertable", new=MagicMock(return_value=True)
    )
    def test_middleware_ignores_missing_content_length_header(self):
        """
        Test that the middleware appends djCbv markup even if no
        Content-Length header exists.
        """

        # Arrange
        html_content = "<html><head></head><body><p>test</p></body></html>"
        response = create_autospec(HttpResponse)
        response.charset = "utf-8"
        response.content = bytes(html_content, response.charset)
        response.__contains__.return_value = False  # "Content-Length" in response
        self.mock_get_response.return_value = response

        # Act
        res = self.middleware(self.request)

        # Assert
        self.assertTrue('id="djCbv"' in res.content)

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=True)
    )
    @patch.object(DjCbvInspectMiddleware, "_add_djcbv_mixin")
    def test_middleware_process_view_hook_appends_mixin(self, mock_add_mixin):
        """
        Test that the `process_view` hook runs when `should_process_request`
        is True.

        Even if the middleware exits early in `__call__`, the `get_response()` call
        still triggers the `process_view` hook, hence the secondary check here.
        """

        # Act
        self.middleware.process_view(self.request, MagicMock(), (), {})

        # Assert
        mock_add_mixin.assert_called_once()

    @patch.object(
        DjCbvInspectMiddleware, "should_process_request", new=MagicMock(return_value=False)
    )
    @patch.object(DjCbvInspectMiddleware, "_add_djcbv_mixin")
    def test_middleware_process_view_hook_does_not_append_mixin(self, mock_add_mixin):
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
    """
    Client end-to-end request/response tests for the `DjCbvInspectMiddleware` middleware class.
    """

    def test_client_request_for_fbv_returns_early(self):
        """
        Test a function-based view to make sure the toolbar is not shown.
        """

        # Arrange
        client = Client()

        # Act
        response = client.get("/simple_fbv_render")

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_returns_early_when_excluded_with_mixin(self):
        """
        Test excluding a class-based view using the `DjCbvExcludeMixin` mixin class
        and asserting that the toolbar is not shown.
        """

        # Arrange
        client = Client()

        # Act
        response = client.get("/djcbv_exclude_mixin")

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_returns_early_when_excluded_with_decorator(self):
        """
        Test an excluded class-based view using the `djcbv_exclude` decorator function
        and asserting that the toolbar is not shown.
        """

        # Arrange
        client = Client()

        # Act
        response = client.get("/djcbv_exclude_dec")

        # Assert
        self.assertFalse('id="djCbv"' in response.content.decode(response.charset))

    def test_client_request_for_cbv_shows_toolbar(self):
        """
        Test a class-based view request and assert that:
            - the djCbv markup is in the response content
            - the `DjCbvInspectMixin` class has been removed view class
        """

        # Arrange
        client = Client()

        # Act
        response = client.get("/simple_cbv_render")

        # Assert
        self.assertTrue('id="djCbv"' in response.content.decode(response.charset))
        bases = resolve(response._request.path).func.view_class.__bases__
        self.assertTrue(DjCbvInspectMixin not in bases)
