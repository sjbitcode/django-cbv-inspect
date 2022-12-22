from unittest.mock import patch, Mock

from django.test import RequestFactory, TestCase

from django_cbv_inspect.mixins import DjCbvInspectMixin

from . import views


@patch('django_cbv_inspect.utils.serialize_params')
@patch('django_cbv_inspect.utils.get_path')
@patch('django_cbv_inspect.utils.get_super_calls')
@patch('django_cbv_inspect.utils.get_ccbv_link')
class TestDjCBVInspectMixin(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/simple_cbv_render')

        # DjCBVInspectMixin only cares about the logs attr
        self.request._djcbv_inspect_metadata = Mock(logs={})
        self.view_func = views.RenderHtmlView.as_view()
        self.view_func.view_class.__bases__ = (
            DjCbvInspectMixin,
            *self.view_func.view_class.__bases__
        )

    @patch('django_cbv_inspect.utils.get_request')
    def test_mixin_runs_on_get_context_data(
        self,
        mock_utils_get_request,
        mock_utils_serialize_params,
        mock_utils_get_path,
        mock_utils_get_super_calls,
        mock_utils_get_ccbv_link,
    ):
        # Arrange
        mock_utils_get_request.return_value = self.request

        # Act
        response = self.view_func(self.request)
        original_request = response._request
        request_logs = original_request._djcbv_inspect_metadata.logs

        # Assert
        self.assertTrue(len(request_logs) > 0)
        mock_utils_get_request.assert_called()
        mock_utils_serialize_params.assert_called()
        mock_utils_get_path.assert_called()
        mock_utils_get_super_calls.assert_called()
        mock_utils_get_ccbv_link .assert_called()
