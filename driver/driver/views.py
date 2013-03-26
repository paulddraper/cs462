from datetime import datetime
import json
from geopy.distance import GreatCircleDistance
import requests
import sys
import time

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

import foursquare.views
import sms.views
from sms.forms import SMSUserForm
from driver.forms import *


def get_current_driver(request):
	return foursquare.views.getCurrentFSQUser(request).driver


def index(request):
	driver_infos = [foursquare.views.getFSQUserInfo(driver.fsq_user.access_token) for driver in Driver.objects.all()]
	return render(request, 'driver/index.html', {'driver_infos':driver_infos})


def create_driver(fsq_user):
	sms_user = SMSUser()
	sms_user.save()
	driver = Driver(fsq_user=fsq_user, sms_user=sms_user)
	driver.save()
	d_form = DriverForm(instance=driver)
	s_form = SMSUserForm(instance=sms_user)
	return redirect(reverse('driver.views.edit_driver'))


def edit_driver(request):
	driver = get_current_driver(request)
	if request.method == 'POST':
		d_form = DriverForm(request.POST, instance=driver)
		s_form = SMSUserForm(request.POST, instance=driver.sms_user)
		if d_form.is_valid() and s_form.is_valid():
			d_form.save()
			s_form.save()
			return redirect(reverse('driver.views.deliveries'))
	else:	
		d_form = DriverForm(instance=driver)
		s_form = SMSUserForm(instance=driver.sms_user)
	d = {
		'd_form' : d_form,
		's_form' : s_form,
	}
	return render(request, 'driver/edit_driver.html', d)


def deliveries(request):
	deliveries = Delivery.objects.filter(driver=get_current_driver(request))
	return render(request, 'driver/deliveries.html', {'deliveries':deliveries})


def shops(request):
	shops = FlowerShop.objects.filter(driver=get_current_driver(request))
	return render(request, 'driver/shops.html', {'shops':shops})


def add_shop(request):
	if request.method == 'POST':
		form = FlowerShopForm(request.POST)
		if form.is_valid():
			shop = form.save(commit=False)
			shop.driver = get_current_driver(request)
			shop.save()
			return redirect(reverse('driver.views.shops'))
	else:
		driver = foursquare.views.getCurrentFSQUser(request).driver
		form = FlowerShopForm(initial={'driver':driver})
	d = {
		'form' : form,
	}
	return render(request, 'driver/add_shop.html', d)


def edit_shop(request, shop_pk):
	shop = FlowerShop.objects.get(pk=shop_pk)
	if request.method == 'POST':
		form = FlowerShopForm(request.POST, instance=shop)
		if form.is_valid():
			form.save()
			return redirect(reverse('driver.views.shops'))
	else:
		form = FlowerShopForm(instance=shop)
	return render(request, 'driver/edit_shop.html', {'form':form})


# received an sms 'bid'
def bid_sms(sms_user):
	delivery = Delivery.objects.filter(driver__sms_user=sms_user).order_by('-id')[:1].get()
	send_bid(delivery)


# received an sms 'done'
def done_sms(sms_user):
	delivery = Delivery.objects.filter(driver__sms_user=sms_user).order_by('-id')[:1].get()
	delivery.status = 'delivered'
	delivery.save()
	d = {
		'_domain' : 'delivery',
		'_name' : 'complete',
		'delivery_id' : delivery.deliveryid,
		'delivered' : time.mktime(timezone.now().timetuple())
	}
	h = {'Content-type':'application/json',}
	requests.post(delivery.shop.esl, data=json.dumps(d), headers=h)


# make a bid
def send_bid(delivery):
	delivery.status = 'bid'
	delivery.save()
	driver = delivery.driver
	shop = delivery.shop

	d = {
		'_domain' : 'rfq',
		'_name' : 'bid_available',
		'bid_id' : delivery.id,
		'delivery_id' : delivery.deliveryid,
		'amount' : 5,
		'estimated' : time.mktime(delivery.delivery.timetuple()),
	}
	h = {'Content-type':'application/json',}
	requests.post(shop.esl, data=json.dumps(d), headers=h)


@require_POST
def event_signal(request, shop_pk):
	shop = FlowerShop.objects.get(pk=shop_pk)
	driver = shop.driver
	dist = GreatCircleDistance((shop.lat, shop.lng), (driver.fsq_user.lat, driver.fsq_user.lng)).miles
	data = json.loads(request.raw_post_data)
	if data['_domain'] == 'rfq' and data['_name'] == 'delivery_ready':
		bid = (dist <= driver.max_miles)
		delivery = Delivery(
			driver=driver,
			shop=shop,
			pickup=datetime.utcfromtimestamp(int(float(data['pickup']))),
			delivery=datetime.utcfromtimestamp(int(float(data['delivery']))),
			deliveryid=data['delivery_id'],
			address=data['address'],
			lat=data['lat'],
			lng=data['lng'],
			desc=data['desc'],
		)
		delivery.save()
		
		seconds = int(float(data['pickup'])) - time.time()
		pickup_str = 'in %dh%dm' % (seconds % (60*60), seconds / 60 % 60) if seconds > 0 else 'right now'
		if bid:
			send_bid(delivery)
			message = 'Automatic bid for delivery from %s (%.1f miles) for %s. Pickup %s' % (shop.name, dist, delivery.address, pickup_str)
		else:
			message = 'Delivery ready from %s (%.1f miles) for %s. Pickup %s' % (shop.name, dist, delivery.address, pickup_str)
		sms.views.send(driver.sms_user, message)

	elif data['_domain'] == 'rfq' and data['_name'] == 'bid_awarded':
		delivery = Delivery.objects.get(id=data['bid_id'], shop__pk=shop_pk)
		delivery.status = 'awarded'
		delivery.save()
		
		seconds = time.mktime(delivery.pickup.timetuple()) - time.time()
		pickup_str = 'in %dh%dm' % (seconds % (60*60), seconds / 60 % 60) if seconds > 0 else 'right now'
		message = 'Bid awarded for delivery from %s (%.1f miles) for %s. Pickup %s' % (shop.name, dist, delivery.address, pickup_str)	
		sms.views.send(driver.sms_user, message)
		
	elif data['_domain'] == 'delivery' and data['_name'] == 'picked_up':
		delivery = Delivery.objects.get(deliveryid=data['delivery_id'], shop__pk=shop_pk)
		delivery.status = 'picked up'
		delivery.save()
		
	return HttpResponse(200)
