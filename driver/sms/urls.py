from django.conf.urls import patterns, url

urlpatterns = patterns('sms.views',
    url(r'^receive/$', 'receive'),
)
