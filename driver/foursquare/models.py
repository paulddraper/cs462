from django.db import models


class FSQUser(models.Model):
	fsq_id = models.IntegerField(primary_key=True)
	access_token = models.CharField(max_length=200)
	lat = models.FloatField(blank=True, null=True)
	lng = models.FloatField(blank=True, null=True)

from django.contrib import admin

admin.site.register(FSQUser)