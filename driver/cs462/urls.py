from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^', include('driver.urls')),
    url(r'^foursquare/', include('foursquare.urls')),
    url(r'^sms/', include('sms.urls')),

    #Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    #Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

from startup import *