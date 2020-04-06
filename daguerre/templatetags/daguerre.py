from __future__ import absolute_import
import re

from django import template
from django.conf import settings
from django.template.defaultfilters import escape
import six

from daguerre.adjustments import registry
from daguerre.helpers import adjust, AdjustmentInfoDict


register = template.Library()
kwarg_re = re.compile(r"(\w+)=(.+)")


class AdjustmentNode(template.Node):
    def __init__(self, image, adjustments, asvar=None):
        self.image = image
        self.adjustments = adjustments
        self.asvar = asvar

    def render(self, context):
        adjusted = adjust(self.image.resolve(context))

        for adj_to_resolve, kwargs_to_resolve in self.adjustments:
            adj = adj_to_resolve.resolve(context)
            kwargs = dict((k, v.resolve(context))
                          for k, v in six.iteritems(kwargs_to_resolve))
            try:
                adjusted = adjust(adjusted, adj, **kwargs)
            except (KeyError, ValueError):
                if settings.TEMPLATE_DEBUG:
                    raise
                if self.asvar is not None:
                    context[self.asvar] = AdjustmentInfoDict()
                return ''

        # Since this is used for a single image, we just need the info dict
        # for the first image in the helper.
        info_dict = adjusted[0][1]
        if self.asvar is not None:
            context[self.asvar] = info_dict
            return ''
        return escape(info_dict)


class BulkAdjustmentNode(template.Node):
    def __init__(self, iterable, adjustments, asvar):
        self.iterable = iterable
        self.adjustments = adjustments
        self.asvar = asvar

    def render(self, context):
        iterable = self.iterable.resolve(context)

        adj_list = []
        for adj, kwargs in self.adjustments:
            adj_list.append((adj.resolve(context),
                             dict((k, v.resolve(context))
                                  for k, v in six.iteritems(kwargs))))

        # First adjustment *might* be a lookup.
        # We consider it a lookup if it is not an adjustment name.
        if adj_list and adj_list[0][0] in registry:
            lookup = None
        else:
            lookup = adj_list[0][0]
            adj_list = adj_list[1:]
        adjusted = adjust(iterable, lookup=lookup)

        for adj, kwargs in adj_list:
            try:
                adjusted = adjust(adjusted, adj, **kwargs)
            except (KeyError, ValueError):
                if settings.TEMPLATE_DEBUG:
                    raise
                context[self.asvar] = []
                return ''

        context[self.asvar] = adjusted
        return ''


def _get_adjustments(parser, tag_name, bits):
    """Helper function to get adjustment defs from a list of bits."""
    adjustments = []
    current_kwargs = None

    for bit in bits:
        match = kwarg_re.match(bit)
        if not match:
            current_kwargs = {}
            adjustments.append((parser.compile_filter(bit), current_kwargs))
        else:
            if current_kwargs is None:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to `%s` tag" % tag_name)
            key, value = match.groups()
            current_kwargs[str(key)] = parser.compile_filter(value)

    return adjustments


@register.tag(name="adjust")
def adjust_tag(parser, token):
    """
    Returns a url to the adjusted image, or (with ``as``) stores a dictionary
    in the context with ``width``, ``height``, and ``url`` keys for the
    adjusted image.

    Syntax::

        {% adjust <image> <adj> <key>=<val> ... <adj> <key>=<val> [as <varname>] %}

    ``<image>`` should resolve to an image file (like you would get as an
    ImageField's value) or a direct storage path for an image.

    Each ``<adj>`` should resolve to a string which corresponds to a
    registered adjustment. The key/value pairs following each ``<adj>`` will
    be passed into it on instantiation. If no matching adjustment is
    registered or the arguments are invalid, the adjustment will fail.

    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 2:
        raise template.TemplateSyntaxError(
            '"{0}" template tag requires at'
            ' least two arguments'.format(tag_name))

    image = parser.compile_filter(bits[1])
    bits = bits[2:]
    asvar = None

    if len(bits) > 1:
        if bits[-2] == 'as':
            asvar = bits[-1]
            bits = bits[:-2]

    return AdjustmentNode(
        image,
        _get_adjustments(parser, tag_name, bits),
        asvar=asvar)


@register.tag
def adjust_bulk(parser, token):
    """
    Stores a variable in the context mapping items from the iterable
    with adjusted images for those items.

    Syntax::

        {% adjust_bulk <iterable> [<lookup>] <adj> <key>=<val> ... as varname %}

    The keyword arguments have the same meaning as for :ttag:`{% adjust %}`.

    ``<lookup>`` is a string with the same format as a template variable (for
    example, ``"get_profile.image"``). The lookup will be performed on each
    item in the ``iterable`` to get the image or path which will be adjusted.

    Each ``<adj>`` should resolve to a string which corresponds to a
    registered adjustment. The key/value pairs following each ``<adj>`` will
    be passed into it on instantiation. If no matching adjustment is
    registered or the arguments are invalid, the adjustment will fail.

    """
    bits = token.split_contents()
    tag_name = bits[0]

    if len(bits) < 4:
        raise template.TemplateSyntaxError(
            '"{0}" template tag requires at'
            ' least four arguments'.format(tag_name))

    if bits[-2] != 'as':
        raise template.TemplateSyntaxError(
            'The second to last argument to'
            ' {0} must be "as".'.format(tag_name))

    iterable = parser.compile_filter(bits[1])
    asvar = bits[-1]
    adjustments = _get_adjustments(parser, tag_name, bits[2:-2])

    return BulkAdjustmentNode(iterable, adjustments, asvar)
