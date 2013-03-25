import sys

from twilio import twiml
from twilio.rest import TwilioRestClient

from django.conf import settings
from django import http
from django.views.decorators.http import require_POST

import driver.views
from sms.models import *

# send an SMS
def send(sms_user, message):
	client = TwilioRestClient(settings.SMS_SID, settings.SMS_TOKEN)
	client.sms.messages.create(
		body=message[:160],
		to=phone_to_e164(sms_user.phone),
		from_=settings.SMS_PHONE
	)

# called by Twilio when an SMS is received
@require_POST
def receive(request):
	print >> sys.stderr, request.POST['Body']
	assert request.POST['AccountSid'] == settings.SMS_SID

	sms_user = SMSUser.objects.get(phone=e164_to_phone(request.POST['From']))
	if 'bid' in request.POST['Body'].lower():
		driver.views.bid_sms(sms_user)
		
	elif 'done' in request.POST['Body'].lower():
		driver.views.done_sms(sms_user)

	return http.HttpResponse(200, str(twiml.Response()))

# +11234567890 to 123-456-7890
def e164_to_phone(e164):
	return '%s-%s-%s' % (e164[2:5], e164[5:8], e164[8:12])


# 123-456-7890 to +11234567890
def phone_to_e164(phone):
	return '+1%s%s%s' % (phone[0:3], phone[4:7], phone[8:12])
