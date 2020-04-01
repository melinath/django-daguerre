from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
try:
    from django.urls import reverse
except ImportError:
    # Compatibility for Django < 1.10
    from django.core.urlresolvers import reverse


class AreaWidget(AdminFileWidget):
    class Media:
        css = {
            'all': ('imgareaselect/css/imgareaselect-animated.css',
                    'daguerre/css/areawidget.css',)
        }
        js = (
            'imgareaselect/scripts/jquery.imgareaselect.js',
            'daguerre/js/areawidget.daguerre.js',
        )

    def render(self, name, value, attrs=None):
        content = super(AreaWidget, self).render(name, value, attrs)
        if value and hasattr(value, 'url'):
            content += (
                "<div class='daguerre-areas' id='{0}-areas'"
                " data-storage-path='{1}' data-width='{2}' data-height='{3}'"
                " data-url='{4}' data-area-url='{5}'></div>").format(
                    name,
                    value.name,
                    value.width,
                    value.height,
                    reverse(
                        'daguerre_ajax_adjustment_info',
                        kwargs={'storage_path': value.name}),
                    reverse(
                        'daguerre_ajax_update_area',
                        kwargs={'storage_path': value.name}))
        return mark_safe(content)
