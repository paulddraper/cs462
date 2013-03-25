from django.conf.urls import patterns, url

urlpatterns = patterns('driver.views',
    url(r'^$', 'index'),
    url(r'^deliveries/$', 'deliveries'),
    url(r'^shops/$', 'shops'),
    url(r'^add_shop/$', 'add_shop'),
    url(r'^edit_shop/(\d+)/$', 'edit_shop'),
    url(r'^event_signal/(\d+)/$', 'event_signal'),
    url(r'^edit_driver/$', 'edit_driver'),
)
