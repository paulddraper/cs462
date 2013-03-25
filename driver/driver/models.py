from django.db import models
from django.core import validators

from foursquare.models import FSQUser
from sms.models import SMSUser

class Driver(models.Model):
	fsq_user = models.OneToOneField(FSQUser, editable=False)
	sms_user = models.OneToOneField(SMSUser, editable=False)
	max_miles = models.FloatField(default=0)


class FlowerShop(models.Model):
	driver = models.ForeignKey(Driver, editable=False)
	name = models.CharField(max_length=100)
	lat= models.FloatField(
		validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90),]
	)
	lng = models.FloatField(
		validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180),]
	)
	esl = models.URLField(blank=True, null=True)

	def __unicode__(self):
		return '%s''s %s' % (driver.user, self.name)

	class Meta:
		ordering = ['name']


class Delivery(models.Model):
	driver = models.ForeignKey(Driver)
	shop = models.ForeignKey(FlowerShop)
	deliveryid = models.IntegerField()
	pickup = models.DateTimeField(null=True, blank=True)
	delivery = models.DateTimeField(null=True, blank=True)
	address = models.CharField(max_length=200)
	lat= models.FloatField(
		validators=[validators.MaxValueValidator(90), validators.MinValueValidator(-90),]
	)
	lng = models.FloatField(
		validators=[validators.MaxValueValidator(180), validators.MinValueValidator(-180),]
	)
	desc = models.CharField(max_length=400)
	status = models.CharField(max_length=35, null=True, blank=True)

from django.contrib import admin

admin.site.register(Driver)
admin.site.register(FlowerShop)
admin.site.register(Delivery)
