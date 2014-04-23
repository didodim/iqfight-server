from django.db import models
from django.contrib.auth.models import User
import datetime, random

class GameConstants(models.Model):
    questions_in_game   = models.IntegerField(default=10)
    time_for_answer     = models.IntegerField(default=60*1000)
    refresh_interval    = models.IntegerField(default=1*1000)
    
class Question(models.Model):
    question    = models.TextField(default="")
    explanation = models.TextField(default="")
    picture     = models.FilePathField()
    source      = models.CharField(max_length=200,default='')
    
class Answer(models.Model):
    type        = models.CharField(max_length=20)
    order       = models.SmallIntegerField(default=0)
    answer      = models.CharField(max_length=200)
    is_correct  = models.BooleanField(default=False)
    question    = models.ForeignKey(Question)
    
class Game(models.Model):
    name        = models.CharField(max_length=50)
    is_active   = models.BooleanField(default=True)
    date_time   = models.DateField()
    questions    = models.CommaSeparatedIntegerField(max_length=255)
    current_question = models.IntegerField(default=0)
    last_answered   = models.ForeignKey("Player",null=True)
    num_of_players  = models.IntegerField(default=0)
    def save(self,*args,**kwargs):
        if not self.questions:
            constants = GameConstants.objects.all()[0]
            lst = Question.objects.order_by('?').values_list("pk",flat=True)[:constants.questions_in_game]
            self.questions = str(lst)[1:-1]
        if not self.date_time:
            self.date_time = datetime.datetime.now()
        super(self.__class__,self).save(*args,**kwargs)

        
class Player(models.Model):
    user    = models.ForeignKey(User)
    points  = models.IntegerField(default=0)
    current_game = models.ForeignKey(Game,null=True)
    
class PlayerGames(models.Model):
    player  = models.ForeignKey(Player,related_name="games")
    game    = models.ForeignKey(Game,related_name="players")
    points  = models.IntegerField(default=0)
    started = models.DateField()
    ended   = models.DateField(null=True)
    
        
    
