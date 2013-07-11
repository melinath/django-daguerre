from django.conf.urls import patterns, url

from daguerre.views import (AdjustedImageRedirectView, AjaxAdjustmentInfoView,
                            AjaxUpdateAreaView)


urlpatterns = patterns(
    '',
    url(r'^adjust/(?P<storage_path>.+)$',
        AdjustedImageRedirectView.as_view(),
        name="daguerre_adjusted_image_redirect"),
    url(r'^info/(?P<storage_path>.+)$',
        AjaxAdjustmentInfoView.as_view(),
        name="daguerre_ajax_adjustment_info"),
    url(r'^area/(?P<storage_path>.+?)(?:/(?P<pk>\d+))?$',
        AjaxUpdateAreaView.as_view(),
        name="daguerre_ajax_update_area"),
)
