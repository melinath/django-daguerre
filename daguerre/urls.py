from django.conf.urls.defaults import patterns, url
from daguerre.views import AdjustedImageRedirectView, AjaxAdjustmentInfoView

urlpatterns = patterns('',
	url(r'^adjust/(?P<storage_path>.+)$', AdjustedImageRedirectView.as_view(), name="daguerre_adjusted_image_redirect"),
	url(r'^info/(?P<storage_path>.+)$', AjaxAdjustmentInfoView.as_view(), name="daguerre_ajax_adjustment_info"),
)