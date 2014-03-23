from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

urlpatterns = (
    static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) +
    patterns('',
    	url(r'^', include('daguerre.urls')),
    	url(r'^admin/', include(admin.site.urls)),
    )
)
