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

	def avg_delay(self):
		return self.delivery_set.filter(esl=

	def __unicode__(self):
		return self.user.get_full_name()

	def delay_avgs():
		return (Driver.objects
			.filter(bid__delivery__accepted=models.F('bid'))
			.exclude(bid__delivery__delivered=None)
			.annotate(avg_delay=Avg('bid__delay'))
		)

class Delivery(models.Model):
	store = models.ForeignKey(Store)
	delivery = models.DateTimeField(blank=True, null=True, default=timezone.now)
	delivered = models.DateTimeField(blank=True, null=True)
	delivery_id = modesl.IntegerField()
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
