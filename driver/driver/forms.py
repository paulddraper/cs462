from django import forms

from driver.models import *

class DriverForm(forms.ModelForm):
	class Meta:
		model = Driver

class FlowerShopForm(forms.ModelForm):
	class Meta:
		model = FlowerShop