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
        if PlayerGames.objects.filter(player=player,is_current=True).exclude(game=game):
            return get_response(request, {'players_to_start': -1,
                                  'status':'error','error_message':'You are playing another game!!!'})
        pg,created = PlayerGames.objects.get_or_create(player=player,game=game,is_current=True)
        if created:
            game.num_of_players += 1
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
    try:
        user = request.user
        pg = PlayerGames.objects.select_related('game','player').get(player__user=user,is_current=True)
        game = pg.game
        pgs = PlayerGames.objects.select_related().filter(game=game,is_current=True)
        res = {'is_blocked':pg.is_blocked(),'status':'ok','error_message':''}
        const = GameConstants.objects.all()[0]
        if not game.question_started:
            game.question_started = datetime.datetime.now() + datetime.timedelta(milliseconds=500)
            game.save()
        delta = datetime.datetime.now() - game.question_started + datetime.timedelta(milliseconds=200)
        ms = delta.days*24*60*60*1000 + delta.seconds*1000 + delta.microseconds/1000
        res['remaing_time'] = const.time_for_answer - ms
        if res['remaing_time'] <= 0:
            res['remaing_time'] = 0
        res['answered_user'] = ''
        question = None
        if game.answered:
            res['answered_user'] =  game.answered.user.username
            if game.players_seen_answered == game.max_num_of_players:
                game.players_seen_answered = 0
                pgs.update(seen_answered=False)
                question = game.next_question()
            elif not pg.seen_answered:
                game.players_seen_answered += 1
                game.save()
                pg.seen_answered = True
                pg.save()
                question = game.get_current_question()
        elif res['remaing_time'] <= 0:
            question = game.next_question()
            res['answered_user'] =  'NOBODY'
        else:
            question = game.get_current_question()
        res['refresh_interval'] = const.time_for_answer
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
            pgs.update(is_current=False,ended=datetime.datetime.now())
            res['error_message'] = 'Game over'
            res['status'] = 'error'
            game.set_winner(pgs,False)
            game.save()
        res['users'] = []
        for el in pgs:
            res['users'] += [{"name": el.player.user.username,"points":el.points}]
        return get_response(request,res)
    except PlayerGames.DoesNotExist:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'error','error_message':'Game over','users':[],'remaing_time':-1,'answered_user':'','answers':[],
                             'question':'','refresh_interval':1000}
                            )
    except:
        logger.error(traceback.format_exc())
        return get_response(request,
                            {'status':'error','error_message':'Server Error','users':[],'remaing_time':-1,'answered_user':'','answers':[],
                             'question':'','refresh_interval':1000}
                            )
    
@login_required(login_url='/login')
def answer(request):
    try:
        data = request.GET
        user = request.user
        pg = PlayerGames.objects.select_related('game','player').get(player__user=user,is_current=True)
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
                pg.block(game.current_question)
        return get_response(request,res)
    except PlayerGames.DoesNotExists:
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
        game.save()
        return get_response(request,{'name':game.name,"id":game.pk,"status":'ok','error_message':''})
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'name':'',"id":"","status":'error','error_message':'Server Error'})
    
def quit(request):
    try:
        pgs = PlayerGames.objects.select_related('player','game').filter(player__user=request.user)
        pgs.update(is_current=False)
        for el in pgs:
            if el.game.players_to_start == 0:
                n = el.game.num_of_players
                el.game.init()
                el.game.num_of_players = n-1
                el.game.save()
            else:
                if el.game.num_of_players > 1:
                    el.game.num_of_players -= 1
                    el.game.save()
                else:
                    el.game.delete()
        return get_response(request,{'status':'ok','error_message':''}) 
    except:
        logger.error(traceback.format_exc())
        return get_response(request,{'status':'error','error_message':'Server Error'})

@login_required(login_url='/login')            
def statistics(request):
    data = request.GET
    limit = data['limit']
    offset = data['offset']
    if data.has_key('game'):
        return statistics_game(limit,offset,data['game'])
    else:
        return statistics_all(limit,offset)
    
def statistics_all(limit,offset):
    players = Player.objects.select_related().order_by('-points')[offset:offset+limit] 
    
    
    