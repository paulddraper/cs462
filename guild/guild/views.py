import json
import requests
import sys
import time

from django.contrib import auth
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test, login_required
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
		dform = DriverForm(request.POST)
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
		dform = DriverForm()
	d = {'uform':uform, 'dform':dform,}
	return render(request, 'guild/new_driver.html', d)


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
		dform = DriverForm(instance=request.user.driver)
	d = {
		'uform' : uform,
		'dform' : dform,
	}
	return render(request, 'guild/edit_driver.html', d)

@staff_member_required
def stores(request):
	d = {'stores':Store.objects.all()}
	return render(request, 'guild/stores.html', d)

@staff_member_required
def new_store(request):
	if request.method == 'POST':
		form = StoreForm(request.POST)
		if form.is_valid():
			form.save()
			return redirect(reverse('guild.views.stores'))
	else:
		form = StoreForm()
	d = {'form' : form}
	return render(request, 'guild/new_store.html', d)

@staff_member_required
def edit_store(request, store_pk):
	store = Store.objects.get(pk=store_pk)
	if request.method == 'POST':
		form = StoreForm(request.POST, instance=store)
		if form.is_valid():
			form.save()
			return redirect(reverse('guild.views.stores'))
	else:
		form = StoreForm(instance=store)
	return render(request, 'guild/edit_store.html', {'form':form})

@staff_member_required
def ranking(request):
	d = {'drivers':Driver.delay_avgs()}
	return render(request, 'guild/ranking.html', d)

# called by store website to signal events
@csrf_exempt
@require_POST
def event_signal_store(request, store_pk):
	store = Store.objects.get(pk=store_pk)
	data = json.loads(request.raw_post_data)
	
	if data['_domain'] == 'rfq' and data['_name'] == 'delivery_ready':
		delivery = Delivery(
			store=store,
			delivery=datetime.utcfromtimestamp(int(float(data['delivery']))),
			delivery_id=data['delivery_id']
		)
		delivery.save()
		data['delivery_id'] = delivery.id
		h = {'Content-type':'application/json'}
		for driver in sorted(Driver.delay_avgs(), cmp=lambda x,y: x.avg_delay < y.avg_delay)[:3]:
			requests.post(driver.esl, data=json.dumps(data), headers=h)
	
	elif data['_domain'] == 'rfq' and data['_name'] == 'bid_awarded':
		bid = Bid.objects.get(id=data['bid_id'], delivery__store__pk=store_pk)
		delivery = bid.delivery
		delivery.accepted = bid
		delivery.save()
		bid.driver.status = 'bid awarded'
		bid.driver.save()
		data['delivery_id'] = delivery.id
		data['bid_id'] = bid.bid_id
		h = {'Content-type':'application/json'}
		requests.post(bid.driver.esl, data=json.dumps(data), headers=h)
		
	elif data['_domain'] == 'delivery' and data['_name'] == 'picked_up':
		delivery = Delivery.objects.get(delivery_id=data['delivery_id'], store__pk=store_pk)
		delivery.accepted.driver.status = 'picked up'
		delivery.accepted.driver.save()
		data['delivery_id'] = delivery.id
		h = {'Content-type':'application/json'}
		requests.post(delivery.accepted.driver.esl, data=json.dumps(data), headers=h)
	
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
		driver.status = 'bid'
		driver.save()
		data['bid_id'] = bid.id
		data['delivery_id'] = delivery.delivery_id
		h = {'Content-type':'application/json'}
		requests.post(delivery.store.esl, data=json.dumps(data), headers=h)
	
	elif data['_domain'] == 'delivery' and data['_name'] == 'complete':
		delivery = Delivery.objects.get(id=data['delivery_id'], accepted__driver=driver)
		delivery.delivered = datetime.utcfromtimestamp(int(float(data['delivered']))).replace(tzinfo=timezone.utc)
		delivery.save()
		driver.status = 'delivered'
		driver.save()
		data['delivery_id'] = delivery.delivery_id
		h = {'Content-type':'application/json'}
		requests.post(delivery.store.esl, data=json.dumps(data), headers=h)

	else:
		raise Exception(data)
	
	return HttpResponse(200)

