from django.conf.urls.defaults import patterns, url
from .views import adjusted_image_redirect, ajax_adjustment_info

urlpatterns = patterns('',
	url(r'^adjust/(?P<storage_path>.+)$', adjusted_image_redirect, name="daguerre_adjusted_image_redirect"),
	url(r'^ajax/adjust/info/(?P<ident>.+)$', ajax_adjustment_info, name="daguerre_ajax_adjustment_info"),
)