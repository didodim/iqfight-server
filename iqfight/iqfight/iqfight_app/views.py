from django.shortcuts import render
import json
from django.http import HttpResponse
from iqfight_app.models import *
from django.contrib.auth.models import User 
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
import traceback
from django.core import serializers

def get_response(request,d):
    return HttpResponse(content=json.dumps(obj=d, encoding="UTF-8"), mimetype='application/json')

def get_games(request,user):
    return Game.objects.filter(is_active=True).values('name','id')
    
def is_logged(request):
    if request.user.is_anonymous():
        username = ''
        session_id = ''
    else:
        username = request.user.username
        session_id = request.COOKIES['sessionid']
    d = {'username': username, "session_id":session_id}
    return get_response(request,d)
    
is_logged_response  = {
                       'username': '', 'session_id':''
                       }
def login_func(request):
    user = authenticate(username=request.POST['username'], password=request.POST['password'])
    login(request, user)
    if user:
        return get_response(request,{"logged":True,
                                     "session_id":request.COOKIES['sessionid'],
                                     'username':user.username,
                                     'games':get_games(request,user)})
    else:
        return get_response(request,{"logged":False,
                                     "session_id":request.COOKIES['sessionid'],
                                     'username':'',
                                     'games':[]})
    
login_request = {
    'username':'', 'password':''
}

login_response = {
                  "logged":True, "session_id":'', 'username':'','games':[]
                  
                  }

'open_game?id='

open_game_response = {
                      'players_to_start': 0, 'refresh_interval':1000
                      }
                     
play_response = {
                 'refresh_interval':1000, 'question':'','answers':[],'users':[],'remaing_time':53*1000, 'answered_user':'',
                 }
                    
answer_response = {
                    'refresh_interval':1000,'correct':True,'already_answered':False
                   }

