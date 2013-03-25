from threading import Thread
import json
import requests
import time

from django.conf import settings
from django.contrib import auth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from datetime import datetime

from store.forms import *
from store.models import *

def is_store_user(user):
	return hasattr(user, 'store_user')

def is_delivery_user(user):
	return hasattr(user, 'delivery_user')

store_user_required = user_passes_test(is_store_user)
delivery_user_required = user_passes_test(is_delivery_user)


# General

def main(request):
	if is_store_user(request.user):
		return redirect(reverse('store.views.deliveries'))
	elif is_delivery_user(request.user):
		return redirect(reverse('store.views.edit_delivery_user'))
	return redirect(reverse('django.contrib.auth.views.login'))


# Store-side

@store_user_required
def edit_store_user(request):
	if request.method == 'POST':
		uform = MyUserChangeForm(request.POST, instance=request.user)
		if uform.is_valid():
			uform.save()
	else:
		uform = UserChangeForm(instance=request.user)
	d = {'uform':uform, 'deliveries':Delivery.objects.all(),}
	return render(request, 'store/edit_store_user.html', d)

@store_user_required
def deliveries(request):
	d = {'deliveries':Delivery.objects.all()}
	return render(request, 'store/deliveries.html', d)

@store_user_required
def request_delivery(request):
	if request.method == 'POST':
		data = request.POST.copy()
		try:
			location = requests.get(
				url='http://nominatim.openstreetmap.org/search'
				, params={'q':request.POST['address'], 'format':'json'}
			).json()[0]
			data['address'] = location['display_name']
			data['lat'] = location['lat']
			data['lng'] = location['lon']
			form = DeliveryRequestForm(data)
			if form.is_valid():
				return render(request, 'store/request_delivery_confirm.html', {'form':form})
		except IndexError:
			data['address'] = 'Could not find address'
			form = DeliveryRequestForm(data)
	else:
		form = DeliveryRequestForm()
	return render(request, 'store/request_delivery.html', {'form':form})


# called when user confirms delivery selection
@require_POST
def request_delivery_confirm(request):
	form = DeliveryRequestForm(request.POST)
	if form.is_valid():
		delivery = form.save()
		d = json.dumps({
				'_domain' : 'rfq',
				'_name' : 'delivery_ready',
				'delivery_id' : delivery.id,
				'address' : delivery.address,
				'lat' : delivery.lat,
				'lng' : delivery.lng,
				'pickup' : time.mktime(delivery.pickup.timetuple()),
				'delivery' : time.mktime(delivery.delivery.timetuple()),
				'desc' : delivery.description,
		})
		h = {'Content-type':'application/json'}
		Thread(target=lambda: [
			requests.post(delivery_user.esl, data=d, headers=h)
			for delivery_user
			in DeliveryUser.objects.all()
		]).start()
		return redirect(reverse('store.views.deliveries'))
	return redirect(reverse('store.views.request_delivery'))


# called when store use accepts a bid
@store_user_required
def accept(request, bid_pk):
	bid = Bid.objects.get(pk=bid_pk)
	delivery = bid.delivery
	delivery.accepted = bid
	delivery.save()
	d = json.dumps({
		'_domain' : 'rfq',
		'_name' : 'bid_awarded',
		'bid_id' : bid.bid_id,
	})
	h = {'Content-type':'application/json'}
	Thread(target=lambda:
		request.post(bid.delivery_user.esl, data=d, headers=h)
	).start()
	return redirect(reverse('store.views.deliveries'))


# called when store user indicates that delivery has been picked up
def pickedup(request, delivery_pk):
	delivery = Delivery.objects.get(pk=delivery_pk)
	delivery.pickedup = timezone.now()
	delivery.save()
	d = json.dumps({
		'_domain' : 'delivery',
		'_name' : 'picked_up',
		'delivery_id' : delivery.id,
		'pickedup' : time.mktime(delivery.pickedup.timetuple()),
	})
	h = {'Content-type':'application/json'}
	Thread(target=lambda:
		request.post(delivery.accepted.delivery_user.esl, data=d, headers=h)
	).start()
	return redirect(reverse('store.views.deliveries'))


# Driver-side

def new_delivery_user(request):
	if request.method == 'POST':
		uform = MyUserCreationForm(request.POST)
		dform = DeliveryUserForm(request.POST)
		if uform.is_valid() and dform.is_valid():
			user = uform.save()
			delivery_user = dform.save(commit=False)
			delivery_user.user = user
			delivery_user.save()
			user = auth.authenticate(username=uform.data['username'], password=uform.data['password1'])
			auth.login(request, user)
			return redirect('store.views.edit_delivery_user')
	else:
		uform = MyUserCreationForm()
		dform = DeliveryUserForm()
	d = {'uform':uform, 'dform':dform,}
	return render(request, 'store/new_delivery_user.html', d)


@delivery_user_required
def edit_delivery_user(request):
	if request.method == 'POST':
		uform = MyUserChangeForm(request.POST, instance=request.user)
		dform = DeliveryUserForm(request.POST, instance=request.user.delivery_user)
		if uform.is_valid() and dform.is_valid():
			uform.save()
			dform.save()
	else:
		uform = MyUserCreationForm(instance=request.user)
		dform = DeliveryUserForm(instance=request.user.delivery_user)
	d = {
		'uform' : uform,
		'dform' : dform,
	}
	return render(request, 'store/edit_delivery_user.html', d)


# called by driver website to signal events
@csrf_exempt
@require_POST
def event_signal(request, delivery_user_pk):
	data = json.loads(request.raw_post_data)
	if data['_domain'] == 'rfq' and data['_name'] == 'bid_available':
		delivery = Delivery.objects.get(pk=data['delivery_id'])
		delivery_user = DeliveryUser.objects.get(pk=delivery_user_pk)
		bid = Bid(
			delivery=delivery
			, delivery_user=delivery_user
			, estimated=datetime.utcfromtimestamp(int(float(data['estimated']))).replace(tzinfo=timezone.utc)
			, amount=float(data['amount'])
		).save()
	elif data['_domain'] == 'delivery' and data['_name'] == 'complete':
		delivery = Delivery.objects.get(id=data['delivery_id'], delivery_user__pk=delivery_user_pk)
		delivery.delivered = datetime.utcfromtimestamp(int(float(data['delivered']))).replace(tzinfo=timezone.utc)
		delivery.save()
	return HttpResponse(200)
