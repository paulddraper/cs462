from datetime import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class Store(models.Model):
	esl = models.URLField(blank=True, null=True)

	def __unicode__(self):
		return '%s''s %s' % (esl,)

class Driver(models.Model):
	user = models.OneToOneField(User, related_name='driver')
	esl = models.URLField(verbose_name='event signal URL', blank=True, null=True)

	def __unicode__(self):
		return self.user.get_full_name()

	@staticmethod
	def delay_avgs():
		drivers = list(Driver.objects.all())
		for driver in drivers:
			deliveries = Delivery.filter(accepted=driver.bid).exclude(delivered=None)
			avg_start = deliveries.aggregate(models.Avg('delivery'))
			avg_end = deliveries.aggregate(models.Avg('delivered'))
			driver.avg_dely = (avg_start - avg_end).total_minutes()
		return drivers

class Delivery(models.Model):
	store = models.ForeignKey(Store)
	delivery = models.DateTimeField(blank=True, null=True, default=timezone.now)
	delivered = models.DateTimeField(blank=True, null=True)
	delivery_id = models.IntegerField()
	accepted = models.ForeignKey('Bid', related_name='accepted', null=True)
	
	def delay(self):
		return (delivery - delivered).total_minutes()

class Bid(models.Model):
	delivery = models.ForeignKey(Delivery)
	driver = models.ForeignKey(Driver)
	bid_id = models.IntegerField()


from django.contrib import admin

admin.site.register(Store)
admin.site.register(Driver)
admin.site.register(Delivery)
admin.site.register(Bid)
