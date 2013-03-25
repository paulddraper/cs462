from django.conf.urls import patterns, url

urlpatterns = patterns('guild.views',
    url(r'^$', 'main'),
    url(r'^new_driver/$', 'new_driver'),
    url(r'^edit_driver/$', 'edit_driver'),
    url(r'^stores/$', 'stores'),
    url(r'^new_store/$', 'new_store'),
    url(r'^edit_store/(\d+)/$', 'edit_store'),
    url(r'^ranking/$', 'ranking'),
    url(r'^event_signal/store/(\d+)/$', 'event_signal_store'),
    url(r'^event_signal/driver/(\d+)/$', 'event_signal_driver'),
)

