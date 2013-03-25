import json
import time
import urllib
import urllib2

from django import http
from django.views.decorators.http import require_POST

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render

import driver.views
from foursquare.models import *

# redirects user to Foursquare for authorization
def oauth_auth(request):
	data = urllib.urlencode({
		'client_id' : settings.FSQ_CLIENT_ID,
		'response_type' : 'code',
		'redirect_uri' : settings.FSQ_REDIRECT_URL,
	})
	return http.HttpResponseRedirect('https://foursquare.com/oauth2/authenticate?%s' % (data,))


# called by Foursquare after authorization
def oauth_return(request):
	#code from Foursquare
	code = request.GET['code']

	#get access token
	data = urllib.urlencode({
		'client_id' : settings.FSQ_CLIENT_ID,
		'client_secret' : settings.FSQ_CLIENT_SECRET,
		'grant_type' : 'authorization_code',
		'redirect_uri' : settings.FSQ_REDIRECT_URL,
		'code' : code,
	})
	fsq_req = urllib2.Request('https://foursquare.com/oauth2/access_token', data)
	fsq_resp = urllib2.urlopen(fsq_req)
	fsq_resp_json = json.loads(fsq_resp.read())
	access_token = fsq_resp_json['access_token']

	#get user info
	fsq_user_info = getFSQUserInfo(access_token)

	#create person, as necessary
	try:
		person = FSQUser.objects.get(fsq_id=fsq_user_info['id'])
		person.access_token = access_token
		person.save()
	except FSQUser.DoesNotExist:
		person = FSQUser(fsq_id=fsq_user_info['id'], access_token=access_token)
		person.save()
		return driver.views.create_driver(person)

	#login
	request.session['person_pk'] = person.pk

	#redirect to index
	return redirect(reverse('driver.views.edit_driver'))


# log out of website
def logout(request):
	del request.session['person_pk']
	return redirect(reverse('driver.views.index'))


def getCurrentFSQUser(request):
	return FSQUser.objects.get(pk=request.session['person_pk'])


# get user information from foursquare
def getFSQUserInfo(access_token):
	data = urllib.urlencode({
		'oauth_token' : access_token
	})
	user_url = 'https://api.foursquare.com/v2/users/self?%s' % (data,)
	fsq_resp = urllib2.urlopen(user_url)
	fsq_resp_json = json.loads(fsq_resp.read())
	return fsq_resp_json['response']['user']


# called by Foursquare when checkin happen
@require_POST
def checkin(request):
	assert request.POST['secret'] == settings.FSQ_PUSH_SECRET
	
	checkin_info = json.loads(request.POST['checkin'])
	fsq_user = FSQUser.objects.get(fsq_id=checkin_info['user']['id'])
	
	if 'venue' in checkin_info:
		location = checkin_info['venue']['location']
	elif 'location' in checkin_info:
		location = checkin_info['location']
	else:
		raise Exception('no location')
	fsq_user.lat = location['lat']
	fsq_user.lng = location['lng']
	fsq_user.save()

	return http.HttpResponse('OK', 200)
