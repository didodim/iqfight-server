from django.db import models
from django.contrib.auth.models import User
import datetime

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
    is_active   = models.BooleanField(default=True)
    date_time   = models.DateField()
    current_question = models.ForeignKey(Question)
    
    
