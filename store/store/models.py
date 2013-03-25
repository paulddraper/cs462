from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class StoreUser(models.Model):
	user = models.OneToOneField(User, related_name='store_user')
	
	def __unicode__(self):
		return self.user.get_full_name()

class DeliveryUser(models.Model):
	user = models.OneToOneField(User, related_name='delivery_user')
	esl = models.URLField(verbose_name='event signal URL', blank=True, null=True)

	def __unicode__(self):
		return self.user.get_full_name()

class Delivery(models.Model):
	address = models.CharField(max_length=300)
	lat = models.FloatField()
	lng = models.FloatField()
	pickup = models.DateTimeField(blank=True, null=True, default=timezone.now)
	delivery = models.DateTimeField(blank=True, null=True, default=timezone.now)
	description = models.CharField(blank=True, max_length=1000)
	accepted = models.ForeignKey('Bid', related_name='accepted', blank=True, null=True)
	pickedup = models.DateTimeField(blank=True, null=True)
	delivered = models.DateTimeField(blank=True, null=True)
	
	class Meta:
		ordering = ['pk',]
		
	def __unicode__(self):
		return u'%s %s' % (self.address, self.delivery,)

class Bid(models.Model):
	delivery = models.ForeignKey(Delivery)
	delivery_user = models.ForeignKey(DeliveryUser)
	estimated = models.DateTimeField()
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	bid_id = models.IntegerField()
		
from django.contrib import admin

admin.site.register(StoreUser)
admin.site.register(DeliveryUser)
admin.site.register(Delivery)
admin.site.register(Bid)
