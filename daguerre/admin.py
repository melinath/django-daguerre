from django import forms
from django.contrib import admin
from django.template.loader import render_to_string

from daguerre.models import Image, Area, AdjustedImage


class AreaInline(admin.TabularInline):
	model = Area
	extra = 1


class AdjustedImageForm(forms.ModelForm):
	def __init__(self, *args, **kwargs):
		super(AdjustedImageForm, self).__init__(*args, **kwargs)
		crop = self.fields['requested_crop']
		crop.queryset = crop.queryset.filter(image__pk=self.instance.image_id)


class AdjustedImageBase(object):
	form = AdjustedImageForm
	readonly_fields = ('path', 'as_html', 'width', 'height')
	
	def as_html(self, obj):
		return render_to_string('admin/daguerre/adjustedimage/as_html.html', {'obj': obj})
	as_html.short_description = 'image'
	as_html.allow_tags = True
	
	def path(self, obj):
		if obj.adjusted:
			return "<a href='%s'>%s</a>" % (obj.adjusted.url, obj.adjusted)
		return ''
	path.allow_tags = True
	
	PARAMETER_FIELDS = (
		('requested_width', 'requested_height'),
		('requested_max_width', 'requested_max_height'),
		('requested_adjustment', 'requested_crop')
	)
	IMAGE_FIELDS = ('as_html', 'path', ('width', 'height'))


class AdjustedImageAdmin(AdjustedImageBase, admin.ModelAdmin):
	fieldsets = (
		(None, {
			'fields': ('image',)
		}),
		('Requested parameters', {
			'fields': AdjustedImageBase.PARAMETER_FIELDS,
		}),
		('Generated image', {
			'fields': AdjustedImageBase.IMAGE_FIELDS
		})
	)


class AdjustedImageInline(AdjustedImageBase, admin.StackedInline):
	model = AdjustedImage
	extra = 0
	max_num = 0
	fieldsets = (
		(None, {
			'fields': AdjustedImageBase.PARAMETER_FIELDS
		}),
		('Generated image', {
			'fields': AdjustedImageBase.IMAGE_FIELDS
		})
	)


class ImageAdmin(admin.ModelAdmin):
	inlines = [AreaInline, AdjustedImageInline]
	readonly_fields = ('height', 'width', 'timestamp')
	list_display = ('name', 'timestamp', 'width', 'height')
	date_hierarchy = 'timestamp'
	search_fields = ['name',]
	list_filter = ('width', 'height')
	fieldsets = (
		(None, {
			'fields': ('name', 'image', ('width', 'height', 'timestamp'))
		}),
	)
	
	def save_formset(self, request, form, formset, change):
		"""Delete all fills and crops associated with the image each time that an area is added or changed."""
		formset.save()
		if formset.model == Area:
			for form in formset.forms:
				if form.has_changed():
					request._areas_changed = True
					break
		elif formset.model == AdjustedImage and getattr(request, '_areas_changed', False):
			formset.instance.adjustedimage_set.filter(requested_adjustment__in=['fill', 'crop']).delete()


admin.site.register(Image, ImageAdmin)
admin.site.register(AdjustedImage, AdjustedImageAdmin)