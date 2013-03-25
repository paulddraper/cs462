from django.conf.urls import patterns, url

urlpatterns = patterns('foursquare.views',
    url(r'^callback/$', 'oauth_return'),
    url(r'^login/$', 'oauth_auth'),
    url(r'^logout/$', 'logout'),
    url(r'^checkin/$', 'checkin'),
)
