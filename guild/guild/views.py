import json
import requests
import time

from django.contrib import auth
from django.contrib.auth.decorators import user_passes_test, login_required, staff_member_requred
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime

from guild.forms import *
from guild.models import *

driver_required = user_passes_test(lambda u: u.driver)

# General

@login_required
def main(request):
	if request.user.is_staff:
		return redirect(reverse('guild.views.ranking'))
	elif request.user.driver:
		return redirect(reverse('guild.views.edit_driver'))
	raise Exception() 

def new_driver(request):
	if request.method == 'POST':
		uform = MyUserCreationForm(request.POST)
		dform = DeliveryUserForm(request.POST)
		if uform.is_valid() and dform.is_valid():
			user = uform.save()
			driver = dform.save(commit=False)
			driver.user = user
			driver.save()
			user = auth.authenticate(username=uform.data['username'], password=uform.data['password1'])
			auth.login(request, user)
			return redirect('guild.views.edit_driver')
	else:
		uform = MyUserCreationForm()
		dform = DeliveryUserForm()
	d = {'uform':uform, 'dform':dform,}
	return render(request, 'store/new_driver.html', d)


@driver_required
def edit_driver(request):
	if request.method == 'POST':
		uform = MyUserChangeForm(request.POST, instance=request.user)
		dform = DriverForm(request.POST, instance=request.user.driver)
		if uform.is_valid() and dform.is_valid():
			uform.save()
			dform.save()
	else:
		uform = MyUserCreationForm(instance=request.user)
		dform = DeliveryUserForm(instance=request.user.driver)
	d = {
		'uform' : uform,
		'dform' : dform,
	}
	return render(request, 'store/edit_driver.html', d)

@staff_member_required
def rankings(request):
	d = {'drivers':Driver.delay_avgs()}
	return render(request, 'guild/rankings.html', d)

# called by store website to signal events
@csrf_exempt
@require_POST
def event_signal_store(request, store_pk):
	store = Store.objects.get(pk=store_pk)
	data = json.loads(request.raw_post_data)
	
	if data['_domain'] == 'rfq' and data['_name'] == 'delivery_ready':
		delivery = Delivery(
			store=store,
			delivery=datetime.utcfromtimestamp(int(float(data['delivery']))).replace(tzinfo=timezone.utc),
			delivery_id=data['delivery_id']
		)
		delivery.save()
		data['delivery_id'] = delivery.id
		h = {'Content-type':'application/json'}
		for driver in Driver.delay_avgs().order_by('avg_delay')[:3]:
			requests.post(driver.esl, data=json.dumps(d), headers=h)
	
	elif data['_domain'] == 'rfq' and data['_name'] == 'bid_awarded':
		delivery = Delivery.objects.get(delivery_id=data['delivery_id'], store__pk=store_pk)
		bid = Bid.objects.get(id=data['bid_id'], delivery=delivery)
		delivery.accepted = bid
		delivery.save()
		data['delivery_id'] = delivery.id
		data['bid_id'] = bid.bid_id
		h = {'Content-type':'application/json'}e(tzinfo=timezone.utc)
		requests.post(bid.driver.esl, data=json.dumps(d), headers=h)
		
	elif data['_domain'] == 'delivery' and data['_name'] == 'picked_up':
		delivery = Delivery.objects.get(delivery_id=data['delivery_id'], store__pk=store_pk)
		data['delivery_id'] = delivery.id
		h = {'Content-type':'application/json'}e(tzinfo=timezone.utc)
		requests.post(delivery.accepted.driver.esl, data=json.dumps(d), headers=h)
	
	else:
		raise Exception(data)
	
	return HttpResponse(200)


# called by driver website to signal events
@csrf_exempt
@require_POST
def event_signal_driver(request, driver_pk):
	driver = Driver.objects.get(pk=driver_pk)
	data = json.loads(request.raw_post_data)
	
	if data['_domain'] == 'rfq' and data['_name'] == 'bid_available':
		delivery = Delivery.objects.get(id=data['delivery_id'])
		bid = Bid(
			driver=driver,
			delivery=delivery,
			bid_id=data['bid_id']
		)
		bid.save()
		data['bid_id'] = bid.id
		data['delivery_id'] = delivery.delivery_id
		h = {'Content-type':'application/json'}
		requests.post(delivery.store.esl, data=json.dumps(d), headers=h)
	
	elif data['_domain'] == 'delivery' and data['_name'] == 'complete':
		delivery = Bid.objects.get(bid_id=data['bid_id'], driver=driver).delivery
		delivery.delivered = datetime.utcfromtimestamp(int(float(data['delivered']))).replace(tzinfo=timezone.utc),
		delivery.save()
		data['bid_id'] = bid.id
		data['delivery_id'] = delivery.delivery_id
		h = {'Content-type':'application/json'}
		requests.post(delivery.store.esl, data=json.dumps(d), headers=h)

	else:
		raise Exception(data)
	
	return HttpResponse(200)

