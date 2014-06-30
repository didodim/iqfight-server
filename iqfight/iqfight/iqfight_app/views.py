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
from functools import wraps
from django.db.models import F
logger = log.getLogger(__name__)

def login_required_custom(callback):
    def dec(function):
        def decorator(request, *args, **kwargs):
            if request.user.is_authenticated():
                return function(request, *args, **kwargs)
            else:
                return callback(request, *args, **kwargs)
        return decorator
    return dec

def login_fail(request):
    return get_response(request,{'status':'error',"error_message":"Please log in"})
    

def get_response(request,d):
    return HttpResponse(content=json.dumps(obj=d, encoding="UTF-8"), content_type='application/json')

def get_games_list(player=None):
    
    if not player:
        games = Game.objects.filter(is_active=True,max_num_of_players__gt=F('num_of_players'))
    else:
        try:
            pg = PlayerGames.objects.select_related('game','player').get(player=player,is_current=True)
            games = [pg.game]
        except PlayerGames.DoesNotExist:
            games = Game.objects.filter(is_active=True,max_num_of_players__gt=F('num_of_players'))
    lst = []       
    for el in games:
        lst += [{'id':el.pk,'name':el.name,'players_to_start':el.players_to_start}]
    return lst

def logout_custom(request):
    try:
        logout(request)
        return get_response(request, {"status":"ok","error_message":''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'status':'error','error_message':'Server Error'})
    
def is_logged(request):
    try:
        if request.user.is_anonymous():
            return get_response(request,{'username':'','status':'error','error_message':'Not logged'})
        else:
            return get_response(request,{'username':request.user.username,'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'username':'','status':'error',"error_message":'Server Error'}
                            )
def index(request):
    return HttpResponse(Answer.objects.get(pk=1).picture_url)

def login_func(request):
    try:
        if request.method == 'GET':
            data = request.GET
        else:
            data = request.POST
        user = authenticate(username=data['username'], password=data['password'])
        
        if user:
            login(request, user)
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
        print traceback.format_exc()
        return get_response(request,{"status":"error",
                                         "error_message":'Server Error',
                                         'username':"",
                                         })
def register(request):
    try:
        if request.method == 'GET':
            data = request.GET
        else:
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
    
@login_required_custom(login_fail) 
def get_games(request):
    try:
        player  = Player.objects.get(user=request.user)
        games = get_games_list(player)
        const = GameConstants.objects.all()[0]
        return get_response(request,{'games':games,'refresh_interval':const.refresh_interval_game,'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'games':[],'refresh_interval':1000,'status':'error','error_message':'Server Error'})
    

@login_required_custom(login_fail)
def open_game(request): 
    try:  
        id = request.GET['id']
        game = Game.objects.get(pk=id)
        user = request.user
        player  = Player.objects.get(user=user)
        try:
            pg = PlayerGames.objects.get(player=player,is_current=True)
            if pg.game != game:
                return get_response(request, {'players_to_start': -1,
                                      'status':'error','error_message':'You are playing another game!!!'})
        except PlayerGames.DoesNotExist:
            pg = PlayerGames(player=player,game=game,is_current=True)
            pg.save()
            game.num_of_players += 1
            game.save()
            pg.player.played_games += 1
            pg.player.save()
            
        return get_response(request, {'players_to_start': game.max_num_of_players - game.num_of_players,
                                  'status':'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request, {'players_to_start': -1,
                                  'status':'error','error_message':'Server Error'}) 
    
@login_required_custom(login_fail)
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

@login_required_custom(login_fail)
def play(request):
    try:
        user = request.user
        pg = PlayerGames.objects.select_related('game','player').get(player__user__pk=user.pk,is_current=True)
        game = pg.game
        pgs = PlayerGames.objects.select_related().filter(game=game,is_current=True)
        res = {'is_blocked':pg.is_blocked(),'status':'ok','error_message':'','game_over':False}
        const = GameConstants.objects.all()[0]
        if not game.question_started:
            game.question_started = datetime.datetime.now() + datetime.timedelta(milliseconds=500)
            game.save()
        res['answered_user'] = ''
        question = None
        res['remaing_time'] = game.get_remaining_time(const)
        if game.answered or res['remaing_time'] <= 0:
            waiting = game.get_noquestion_waiting()
            if waiting > 0:
                if game.answered:
                    res['answered_user'] =  game.answered.user.username
                else: 
                    res['answered_user'] =  'NOBODY'
                question = game.get_current_question()
            else:
                question = game.next_question()
        else:
            question = game.get_current_question()
        res['refresh_interval'] = const.time_for_answer
        res['users'] = []
        for el in pgs:
            res['users'] += [{"name": el.player.user.username,"points":el.points}]
        if question:
            res['question'] = {'question': question.question, 
                               'explanation':question.explanation, 
                               'picture': question.picture_url,
                               'number': game.current_question, 
                               'source': question.source}
            res['answers'] = []
            for el in question.answers.all().order_by('order'):
                temp = {'answer':el.answer,'id':el.pk,'picture':el.picture_url}
                res['answers'] += [temp]
        else:
            res['question'] = {}
            res['answers'] = []
            game.is_active = False
            res['game_over'] = True
            game.set_winner(pgs,False)
            game.save()
            pgs.update(is_current=False,ended=datetime.datetime.now())
        
        return get_response(request,res)
    except PlayerGames.DoesNotExist:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'ok','error_message':'','users':[],'remaing_time':-1,'answered_user':'','answers':[],'game_over':True,
                             'question':{},'refresh_interval':1000}
                            )
    except:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'error','error_message':'Server Error','users':[],'remaing_time':-1,'answered_user':'','answers':[],'game_over':False,
                             'question':{},'refresh_interval':1000}
                            )
    
@login_required_custom(login_fail)
def answer(request):
    try:
        data = request.GET
        user = request.user
        pg = PlayerGames.objects.select_related('game','player').get(player__user__pk=user.pk,is_current=True)
        game = pg.game
        res = {'status':'ok','error_message':'','correct':False,'already_answered':False,'answered_user':''}
        if pg.is_blocked():
            return get_response(request,res)
        if game.answered:
            res['answered_user'] =  game.answered.user.username
            res['already_answered'] = True
        else:
            question = game.get_current_question()
            player_answer = question.answers.get(pk=data['answer_id'])
            res['correct'] = player_answer.is_correct
            if res['correct']:
                res['answered_user'] = user.username
                game.answered = pg.player
                game.save()
                pg.got_points(1)
            else:
                pg.block()
        return get_response(request,res)
    except PlayerGames.DoesNotExist:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'error','error_message':'Game over','correct':False,'already_answered':False,'answered_user':''}
                            )
    except:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'error','error_message':'Server Error','correct':'','already_answered':'','answered_user':''}
                            )
def new_game(request):
    try:
        if request.method == 'GET':
            data = request.GET
        else:
            data = request.POST
        game = Game(name=data['name'])
        if data.has_key('players') and data['players']:
            game.max_num_of_players = data['players']
        game.save()
        return get_response(request,{'name':game.name,"id":game.pk,"status":'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'name':'',"id":"","status":'error','error_message':'Server Error'})
    
def quit(request):
    try:
        pgs = PlayerGames.objects.select_related('player','game').filter(player__user__pk=request.user.pk,is_current=True)
        for el in pgs:
            el.game.num_of_players -= 1
            el.game.max_num_of_players -= 1
            el.game.save()
        pgs.update(is_current=False,ended=datetime.datetime.now())
        return get_response(request,{'status':'ok','error_message':''}) 
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'status':'error','error_message':'Server Error'})

@login_required_custom(login_fail)           
def statistics(request):
    try:
        data = request.GET
        limit = data['limit']
        offset = data['offset']
        if data.has_key('game'):
            return statistics_game(limit,offset,data['game'])
        else:
            return statistics_all(limit,offset)
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'status':'error','error_message':'Server Error'})
    
def statistics_all(limit,offset):
    players = Player.objects.select_related().order_by('-points')[offset:offset+limit] 
    res = {'status':'ok','error_message':'','users':[]}
    lst = []
    for el in players:
        lst += [{'usernam':el.user.username,'scores':el.points,'wins':el.wins,'played_games':el.played_games}]
    res['users'] = lst
    return get_response(request,res)
    
def statistics_game(limit,offset,game_id):
    players = PlayerGames.objects.select_related().filter(game__pk=game_id).order_by('-points')[offset:offset+limit] 
    res = {'status':'ok','error_message':'','users':[]}
    lst = []
    for el in players:
        lst += [{'usernam':el.player.user.username,'scores':el.points}]
    res['users'] = lst
    return get_response(request,res) 
