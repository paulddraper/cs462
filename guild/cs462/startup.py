# Startup code
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.conf import settings

from store.models import StoreUser

if not User.objects.filter(username='admin').exists():
    admin = User(
    	username='admin', email='paulddraper@gmail.com',
    	is_staff=True, is_superuser=True,
    	first_name='Store', last_name='Owner'
    )
    admin.set_password('paul')
    admin.save()
    StoreUser(user=admin).save()

site = Site.objects.get_current()
site.domain = 'paul-store.aws.af.cm'
site.save()