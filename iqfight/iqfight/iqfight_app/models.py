from django.db import models
from django.contrib.auth.models import User
import datetime, random

class GameConstants(models.Model):
    questions_in_game   = models.IntegerField(default=10)
    time_for_answer     = models.IntegerField(default=60*1000)
    refresh_interval_game    = models.IntegerField(default=1*1000)
    refresh_interval_play    = models.IntegerField(default=1*1000)
    
class Question(models.Model):
    question    = models.TextField(default="")
    explanation = models.TextField(default="")
    picture     = models.ImageField(upload_to='pictures',null=True)
    source      = models.CharField(max_length=200,default='')
    @property
    def picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            try:
                return self.picture.url
            except ValueError:
                return ''
        return ''
    def __unicode__(self):
        return unicode(self.pk)
     
class Answer(models.Model):
    type        = models.CharField(max_length=20)
    order       = models.SmallIntegerField(default=0)
    answer      = models.TextField(default="")
    picture     = models.ImageField(upload_to='pictures',null=True)
    is_correct  = models.BooleanField(default=False)
    question    = models.ForeignKey(Question,related_name='answers')
    @property
    def picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            try:
                return self.picture.url
            except ValueError:
                return ''
        return ''
    def __unicode__(self):
        return unicode(self.question)+u" order "+unicode(self.order)
class Game(models.Model):
    name        = models.CharField(max_length=50)
    is_active   = models.BooleanField(default=True)
    question_started   = models.DateTimeField(null=True)
    created     = models.DateTimeField()
    questions    = models.CommaSeparatedIntegerField(max_length=255)
    current_question = models.IntegerField(default=0)
    answered    = models.ForeignKey("Player",null=True)
    num_of_players  = models.IntegerField(default=0)
    max_num_of_players = models.IntegerField(default=3)
    question_end = models.DateTimeField(null=True)
    winner = models.ForeignKey("Player",null=True,related_name="game_wins")
    def get_remaining_time(self,const=None):
        if not const:
            const = GameConstants.objects.all()[0]
        delta = datetime.datetime.now() - self.question_started + datetime.timedelta(milliseconds=200)
        ms = delta.days*24*60*60*1000 + delta.seconds*1000 + delta.microseconds/1000
        rem = const.time_for_answer - ms
        if rem < 0:
            rem = 0
        return rem
    def set_winner(self,pgs=None,save=True):
        if not pgs:
            pgs = self.players.select_related().all()
        pg = pgs.order_by("-points")
        self.winner = pg[0].player
        pg[0].player.wins += 1
        pg[0].got_points(5)
        pg[1].got_points(3)
        if save:
            self.save()
            
    def init(self,save=False):
        self.is_active = True
        self.question_started = None
        self.current_question = 0
        self.answered = None
        self.num_of_players = 0
        self.question_end = None
        if save:
            self.save()
    def __unicode__(self):
        return self.name
    @property
    def players_to_start(self):
        return self.max_num_of_players - self.num_of_players
    def save(self,*args,**kwargs):
        constants = GameConstants.objects.all()[0]
        if not self.questions:
            lst = Question.objects.order_by('?').values_list("pk",flat=True)[:constants.questions_in_game]
            self.questions = str(lst).lower().replace('l','')[1:-1]
        if not self.created:
            self.created = datetime.datetime.now()
        if self.max_num_of_players < 0:
            self.max_num_of_players =  3
        if self.num_of_players < 0:
            self.num_of_players = 0
        if self.max_num_of_players == 0:
            self.is_active = False
        super(self.__class__,self).save(*args,**kwargs)
    def get_current_question(self):
        ids = self.get_questions()
        if len(ids) <= self.current_question:
            question =  None
        else:
            question =Question.objects.select_related('answers').get(pk=ids[self.current_question]) 
        return question
    
    def get_questions(self):
        return self.questions.split(',')
    
    def get_noquestion_waiting(self):
        if not self.question_end:
            self.question_end = datetime.datetime.now()
            self.save()
        delta = datetime.datetime.now() - self.question_end + datetime.timedelta(milliseconds=200)
        ms = delta.days*24*60*60*1000 + delta.seconds*1000 + delta.microseconds/1000
        rem = 6000 - ms
        if rem < 0:
            rem = 0
        return rem
    
    def next_question(self):
        ids = self.get_questions()
        self.current_question += 1
        self.answered = None
        self.question_end = None
        if len(ids) <= self.current_question:
            question =  None
            self.is_active = False
        else:
            question = Question.objects.select_related('answers').get(pk=ids[self.current_question])
        self.question_started = datetime.datetime.now() + datetime.timedelta(milliseconds=500)
        self.save()
        return question

        
class Player(models.Model):
    user    = models.ForeignKey(User)
    points  = models.IntegerField(default=0)
    wins    = models.IntegerField(default=0)
    played_games = models.IntegerField(default=0)
    def __unicode__(self):
        return unicode(self.user) 
    
class PlayerGames(models.Model):
    player  = models.ForeignKey(Player,related_name="games")
    game    = models.ForeignKey(Game,related_name="players")
    points  = models.IntegerField(default=0)
    is_current = models.BooleanField(default=True)
    started = models.DateTimeField()
    ended   = models.DateTimeField(null=True)
    block_question = models.SmallIntegerField(null=True)
    def save(self,*args,**kwargs):
        if not self.started:
            self.started = datetime.datetime.now()
        super(self.__class__,self).save(*args,**kwargs)
    def got_points(self,points):
        self.points += points
        self.save()
        self.player.points += points
        self.player.save()
    def block(self,save=True):
        self.block_question = self.game.current_question
        if save:
            self.save()
    def is_blocked(self):
        return (self.game.answered != None) or (self.block_question != None and self.game.current_question != None and self.block_question == self.game.current_question)
    
    def __unicode__(self):
        return unicode(self.player) +u' played '+ unicode(self.game) 

        
    
