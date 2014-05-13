from django.contrib import admin
from iqfight_app.models import *

admin.site.register((GameConstants, Question, Answer))
