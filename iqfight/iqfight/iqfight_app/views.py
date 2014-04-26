from django.shortcuts import render
import json
from django.http import HttpResponse
from iqfight_app.models import *
from django.contrib.auth.models import User 
from django.contrib.auth import login,logout,authenticate
from django.contrib.auth.decorators import login_required
import traceback,datetime
from django.core import serializers
from django.http import *

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
    if request.method == 'GET':
        return is_logged(request)
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
@login_required(login_url='/login')
def open_game(request):   
    id = request.GET['id']
    game = Game.objects.get(pk=id)
    const = GameConstants.objects.all()[0]
    
    if game.max_num_of_players - game.num_of_players < 1:
        return get_response(request,{'players_to_start': -1, 'refresh_interval':const.refresh_interval})
    
    user = request.user
    player  = Player.objects.get(user=user)
    pg,created = PlayerGames.objects.get_or_create(player=player,game=game,is_active=True)
    if created:
        game.num_of_players += 1
    if game.num_of_players == game.max_num_of_players and not game.question_started:
        game.question_started = datetime.datetime.now()
        game.save()
        return HttpResponseRedirect('/play')
    game.save()
    return get_response(request, {'players_to_start': game.max_num_of_players - game.num_of_players,
                                  'refresh_interval':const.refresh_interval})
    
'open_game?id='

open_game_response = {
                      'players_to_start': 0, 'refresh_interval':1000
                      }
    
@login_required(login_url='/login')
def play(request):
    user = request.user
    pg = PlayerGames.objects.select_related('game','player').get(player__user=user,is_active=True)
    const = GameConstants.objects.all()[0]
    res = {'refresh_interval':const.refresh_interval, 'question':'','answers':[],'users':[],'remaing_time':-1, 'answered_user':'',
                 }
    pgs = PlayerGames.objects.select_related('game','player').filter(game=game,is_active=True)
    if not pg.game.is_active:
        pgs.update(is_active=True)
        return get_response(request,res)
    if pg.game.num_of_players <  pg.game.max_num_of_players:
           return get_response(request, {'players_to_start': pg.game.max_num_of_players - pg.game.num_of_players,
                                  'refresh_interval':const.refresh_interval})
    answered_user = ''
    if pg.game.answered:
        question = pg.game.get_current_question()
        answered_user = pg.game.answered.user.username
    elif datetime.datetime.now() - pg.game.question_started < datetime.timedelta(milliseconds=500):
        question = pg.game.next_question()
        anwered_user = 'Nobody'
    res['answered_user'] = answered_user
    if not question:
        pgs.update(is_active=True)
        if not pg.game.is_active:
            pg.game.is_active = True
            pg.game.save()
        return get_response(request,res)
    player_names = []
    for el in pgs.exclude(pk=pg.pk):
        player_names += [el.player.user.username]
        
    res['question'] = {'question': question.question, 'explanation':question.explanation, 'picture': question.picture, 'source': question.source}
    res['answers'] = question.answers.all().order_by('order').values('id','type','answer')
    res['users'] = player_names
    delta = datetime.datetime.now() - pg.game.question_started - datetime.timedelta(milliseconds=200)
    ms = delta.days*24*60*60*1000 + delta.seconds*1000 + delta.microseconds/1000
    res['remaing_time'] = const.time_for_answer - ms
    res['answered_user'] = anwered_user
    return get_response(request,res)
    
def new_game(request):
    data = request.GET
    Game(name=data['name'])
    
play_response = {
                 'refresh_interval':1000, 'question':'','answers':[],'users':[],'remaing_time':53*1000, 'answered_user':'',
                 }
                    
answer_response = {
                    'refresh_interval':1000,'correct':True,'already_answered':False
                   }

