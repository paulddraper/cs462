from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView

admin.autodiscover()

urlpatterns = patterns('',
	#Static
	 url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),

    # Login accounts
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page':'/'}),
    url(r'^accounts/password_change/$', 'django.contrib.auth.views.password_change', {'post_change_redirect':'/'}),
    url(r'^accounts/password_reset_confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,25})/$', 'django.contrib.auth.views.password_reset_confirm'),
    url(r'^accounts/password_reset/$', 'django.contrib.auth.views.password_reset', {'post_reset_redirect':'store/account/'}),
    url(r'^accounts/password_reset_complete/$', 'django.contrib.auth.views.password_reset_complete'),

    # Store
    url(r'^', include('store.urls')),

    # Admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Admin
    url(r'^admin/', include(admin.site.urls)),
)

from startup import *
