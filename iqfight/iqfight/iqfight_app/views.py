from django.shortcuts import render


is_logged_response  = {
                       'username': '', 'session_id':''
                       }
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