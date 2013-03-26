from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from guild.models import *

class MyUserCreationForm(UserCreationForm):
	first_name = forms.CharField(max_length=30, required=False)
	last_name = forms.CharField(max_length=30, required=False)
	email = forms.EmailField(required=False)

	def save(self, commit=True):
		user = super(MyUserCreationForm, self).save(commit=False)
		user.first_name = self.cleaned_data['first_name']
		user.last_name = self.cleaned_data['last_name']
		user.email = self.cleaned_data['email']
		if commit:
				user.save()
		return user

class MyUserChangeForm(UserChangeForm):
	first_name = forms.CharField(max_length=30, required=False)
	last_name = forms.CharField(max_length=30, required=False)
	email = forms.EmailField(required=False)

	def save(self, commit=True):
		user = super(MyUserChangeForm, self).save(commit=False)
		user.first_name = self.cleaned_data['first_name']
		user.last_name = self.cleaned_data['last_name']
		user.email = self.cleaned_data['email']
		if commit:
				user.save()
		return user

	def clean_password(self):
		return '' # This is a temporary fix for a django 1.4 bug	
	
	class Meta:
		model = User
		exclude = ('is_active', 'is_staff', 'is_superuser', 'password', 'last_login', 'date_joined',)

class DriverForm(forms.ModelForm):
	class Meta:
		model = Driver
		exclude = ('user','status')

class StoreForm(forms.ModelForm):
	class Meta:
		model = Store
