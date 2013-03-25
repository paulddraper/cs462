from django.conf.urls import patterns, url

urlpatterns = patterns('store.views',
    url(r'^$', 'main'),
    url(r'^new_delivery_user/$', 'new_delivery_user'),
    url(r'^edit_store_user/$', 'edit_store_user'),
    url(r'^edit_delivery_user/$', 'edit_delivery_user'),
    url(r'^deliveries/$', 'deliveries'),
    url(r'^request_delivery/$', 'request_delivery'),
    url(r'^request_delivery/confirm$', 'request_delivery_confirm'),
    url(r'^accept/(\d+)/$', 'accept'),
    url(r'^event_signal/(\d+)/$', 'event_signal'),
)

