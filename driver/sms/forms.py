from django import forms

from sms.models import *

class SMSUserForm(forms.ModelForm):
	class Meta:
		model = SMSUser