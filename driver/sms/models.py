from django.contrib.localflavor.us.models import PhoneNumberField
from django.db import models

import pkgutil
class SMSUser(models.Model):
	phone = PhoneNumberField(blank=True, null=True)#unique=True)


from django.contrib import admin

admin.site.register(SMSUser)
