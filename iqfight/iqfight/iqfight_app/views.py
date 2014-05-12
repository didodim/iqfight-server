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
from django.db.utils import IntegrityError
from django.utils import log
logger = log.getLogger(__name__)

def get_response(request,d):
    return HttpResponse(content=json.dumps(obj=d, encoding="UTF-8"), content_type='application/json')

def get_games_list():
    lst = []
    games = Game.objects.filter(is_active=True)
    for el in games:
        lst += [{'id':el.pk,'name':el.name,'players_to_start':el.players_to_start}]
    return lst
    
def is_logged(request):
    try:
        if request.user.is_anonymous():
            return get_response(request,{'username':'','status':'error','error_message':'Not logged'})
        else:
            return get_response(request,{'username':request.user.username,'status':'ok','error_message':''})
    except:
        return get_response(request,
                            {'username':'','status':'error',"error_message":'Server Error'}
                            )

def login_func(request):
    try:
        data = request.POST
        if request.method == 'GET':
            return is_logged(request)
        user = authenticate(username=data['username'], password=data['password'])
        login(request, user)
        if user:
            return get_response(request,{"status":"ok",
                                         "error_message":'',
                                         'username':user.username,
                                         })
        else:
            return get_response(request,{"status":"error",
                                         "error_message":'Wrong User',
                                         'username':"",
                                         })
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{"status":"error",
                                         "error_message":'Server Error',
                                         'username':"",
                                         })
def register(request):
    try:
        data = request.POST
        username=data['username'] 
        password=data['password']
        password1 = data['password1']
        if password1 != password:
            raise ValueError("Custom: Passwords did not match")
        if not password:
            raise ValueError("Custom: Empty password")
        user = User.objects.create_user(username=username,email = username ,password = password)
        if not user:
          return get_response(
                            {'username':'','status':'error',"error_message":'Try Later'}
                            )
        Player(user=user).save()  
        return get_response(request,{'username':username,'status':'ok',"error_message":''})
    except IntegrityError:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'username':'','status':'error',"error_message":'The username is used!'}
                            )
    except ValueError:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'username':'','status':'error',"error_message":'Username/Password is empty'}
                            )
    except:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'username':'','status':'error',"error_message":'Server Error'}
                            )
    
@login_required(login_url='/login')  
def get_games(request):
    try:
        games = get_games_list()
        const = GameConstants.objects.all()[0]
        return get_response(request,{'games':games,'refresh_interval':const.refresh_interval_game,'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'games':[],'refresh_interval':1000,'status':'error','error_message':'Server Error'})
    

@login_required(login_url='/login')
def open_game(request): 
    try:  
        id = request.GET['id']
        game = Game.objects.get(pk=id)
        if game.players_to_start < 1:
            return get_response(request,{'players_to_start': -1, 'status':'error','error_message':'The game is full'})
        user = request.user
        player  = Player.objects.get(user=user)
        pg,created = PlayerGames.objects.get_or_create(player=player,game=game,is_current=True)
        if created:
            game.num_of_players += 1
            if not game.question_started:
                game.question_started = datetime.datetime.now() + datetime.timedelta(milliseconds=700)
            game.save()
        return get_response(request, {'players_to_start': game.max_num_of_players - game.num_of_players,
                                  'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request, {'players_to_start': -1,
                                  'status':'error','error_message':'Server Error'}) 
    
@login_required(login_url='/login')
def refresh_game(request):
    try:  
        id = request.GET['id']
        game = Game.objects.get(pk=id)
        user = request.user
        const = GameConstants.objects.all()[0]
        players = PlayerGames.objects.select_related().filter(game=game,is_current=True,ended__isnull=True)
        users = [el.player.user.username for el in players]
        if game.players_to_start == 0:
            game.is_active = True
            if not game.question_started:
                game.question_started = datetime.datetime.now() + datetime.timedelta(milliseconds=500)
            game.save()
        return get_response(request, {'players_to_start': game.max_num_of_players - game.num_of_players,
                                      'refresh_interval':const.refresh_interval_game,
                                      'users':users,
                                      'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request, {'players_to_start': -1,'users':[],
                                      'status':'error','error_message':'Server Error'}) 

@login_required(login_url='/login')
def play(request):
    user = request.user
    pg = PlayerGames.objects.select_related('game','player').get(player__user=user,is_active=True)
    const = GameConstants.objects.all()[0]
    res = {'refresh_interval':const.refresh_interval, 'question':'',
           'answers':[],'users':[],'remaing_time':-1, 
           'answered_user':'','status':'ok',
           'error_message':''
           }
    pgs = PlayerGames.objects.select_related('game','player').filter(game=game,is_active=True)
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
    game = Game(name=data['name'])
    game.save()
    return get_response(request,{'game':game.name})
    
answer_response = {
                    'refresh_interval':1000,'correct':True,'already_answered':False
                   }

