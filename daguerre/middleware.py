from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware, REASON_NO_REFERER, REASON_BAD_REFERER, REASON_BAD_TOKEN
from django.utils.crypto import constant_time_compare
from django.utils.decorators import decorator_from_middleware
from django.utils.http import same_origin
from django.utils.log import getLogger


logger = getLogger('django.request')


class PrivateAjaxMiddleware(CsrfViewMiddleware):
	"""Essentially a copy of Django's CsrfViewMiddleware, but tweaked to protect any AJAX request. This allows protected private APIs. Comments are also from Django's source code."""
	def process_view(self, request, callback, callback_args, callback_kwargs):
		# CSRF middleware always adds CSRF_COOKIE to request.META - or short-circuits the process by returning a response. (This one's not from Django.)
		if request.is_ajax():
			if request.is_secure():
				# Suppose user visits http://example.com/
				# An active network attacker,(man-in-the-middle, MITM) sends a
				# POST form which targets https://example.com/detonate-bomb/ and
				# submits it via javascript.
				#
				# The attacker will need to provide a CSRF cookie and token, but
				# that is no problem for a MITM and the session independent
				# nonce we are using. So the MITM can circumvent the CSRF
				# protection. This is true for any HTTP connection, but anyone
				# using HTTPS expects better!  For this reason, for
				# https://example.com/ we need additional protection that treats
				# http://example.com/ as completely untrusted.	Under HTTPS,
				# Barth et al. found that the Referer header is missing for
				# same-domain requests in only about 0.2% of cases or less, so
				# we can use strict Referer checking.
				referer = request.META.get('HTTP_REFERER')
				if referer is None:
					logger.warning('Forbidden (%s): %s' % (REASON_NO_REFERER, request.path),
						extra={
							'status_code': 403,
							'request': request,
						}
					)
					return self._reject(request, REASON_NO_REFERER)

					# Note that request.get_host() includes the port
					good_referer = 'https://%s/' % request.get_host()
					if not same_origin(referer, good_referer):
						reason = REASON_BAD_REFERER % (referer, good_referer)
						logger.warning('Forbidden (%s): %s' % (reason, request.path),
							extra={
								'status_code': 403,
								'request': request,
							}
						)
						return self._reject(request, reason)
		
			csrf_token = request.META["CSRF_COOKIE"]

			# check incoming token - use X-CSRFToken, since there is no POST data.
			request_csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')

			if not constant_time_compare(request_csrf_token, csrf_token):
				logger.warning('Forbidden (%s): %s' % (REASON_BAD_TOKEN, request.path),
					extra={
						'status_code': 403,
						'request': request,
					}
				)
				return self._reject(request, REASON_BAD_TOKEN)

		return self._accept(request)
	
	def process_response(self, request, response):
		return response
	
	def _accept(self, request):
		return None


private_ajax = decorator_from_middleware(PrivateAjaxMiddleware)