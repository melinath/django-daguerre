from django.conf.urls.defaults import patterns, url
from .views import adjusted_image, resize_image_file, ajax_resize_info

urlpatterns = patterns('',
	url(r'^resize/(?P<ident>[\w-]+)$', adjusted_image, name="image_resize"),
	url(r'^resize/(?P<ident>.+)$', resize_image_file, name="image_file_resize"),
	url(r'^ajax/resize/info/(?P<ident>.+)$', ajax_resize_info, name="ajax_resize_info"),
)