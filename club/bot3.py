#!/usr/bin/env python3

# -*- coding: utf-8 -*-

from twython import Twython
from scipy.stats import skellam
from urllib.request import FancyURLopener

import psycopg2
import json
import time
import os

# True - prints to screen and tweets
# False - only prints to screen (overrides all other settings)

Tweet = True

# Automatically tweet if home, away or both score goals during time delta

goal_tweet = True

# Automatically tweet if home_reg delta shifts by tweet_delta or greater

change_tweet = False
tweet_delta = 0.05 # 5%

# FIFA's hidden API

matchlive_url = "http://www.fifa.com/Live/common/world-match-centre/livematches.js"

# Stoppage time assumptions
# Generally want these to be conservative

stoppage_1reg = 2
stoppage_2reg = 4

hashtag = "\n\n#LigaBBVA"

def outcome(mu1, mu2, min, up, outcome):

    # 1st half
    if (min <= 45): 
        time_r = (90.0-min)+stoppage_1reg+stoppage_2reg
    # 2nd half
    elif (min <= 90):
        time_r = (90.0-min)+stoppage_2reg
        
    ft = time_r/(90.0+stoppage_1reg+stoppage_2reg)

    if (outcome=="draw"):
        p = skellam.pmf(-up, mu1*ft, mu2*ft)
    elif (outcome == "lose"):
        p = skellam.cdf(-1-up, mu1*ft, mu2*ft)
    else:
        p = skellam.cdf(-1+up, mu2*ft, mu1*ft)

    return(p)

# Using pgpass

try:
    conn = psycopg2.connect("host=localhost dbname=soccer user=clong")    
except:
    print("Database connection failed.")

cur = conn.cursor()

# Twitter app keys

keys = json.loads(open(os.path.expanduser('~/.twitter_keys'), 'r').read())

app_key = keys["app_key"]
app_secret = keys["app_secret"]
oauth_token = keys["oauth_token"]
oauth_token_secret = keys["oauth_token_secret"]

twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)

# No robots, no problem

class MyOpener(FancyURLopener):
    version = 'Mozilla/5.0'

myopener = MyOpener()
    
# Stoppage time - 1.25 minutes 1st half, 3 minutes 2nd half
# To be conservative - 2 minutes 1st half, 4 minutes 2nd half

# Again, this part needs to be automated

match_id = 300329357
ids = [match_id]

names = {}
names[match_id] = ["Deportivo La Coruña","Real Betis"]

team_ids = {}
team_ids[match_id] = [90, 244]

team_name = {}
team_name[90] = "Deportivo La Coruña"
team_name[244] = "Real Betis"

# Possibly for future use

fields = {}
fields[match_id] = "offense_home"

score = {}
score[match_id] = [0, 0]

status = {}
status[match_id] = ""

home_p = {}
home_p[match_id] = None

# Possible status
# Match starting time (local)
# "fifa.lineups"
# "fifa.end1sthalf"
# "fifa.end2ndhalf"
# "result"

select_mu = "select teo.exp_factor*tf.exp_factor*sft.offensive*opd.exp_factor,opo.exp_factor*of.exp_factor*sfo.offensive*ted.exp_factor from club.teams o join club.teams t on (t.club_id,t.year)=('%s',2015) join club._schedule_factors sft on (sft.team_id,sft.year)=(t.club_id,t.year) join club._schedule_factors sfo on (sfo.team_id,sfo.year)=(o.club_id,o.year) join club._factors tf on tf.level='offense_home' join club._factors of on of.level='defense_home' join club._factors teo on (teo.parameter,teo.level)=('offense_league',t.league_key) join club._factors ted on (ted.parameter,ted.level)=('defense_league',t.league_key) join club._factors opo on (opo.parameter,opo.level)=('offense_league',o.league_key) join club._factors opd on (opd.parameter,opd.level)=('defense_league',o.league_key) where (o.club_id,o.year)=('%s',2015);"

mu = {}

print

for id in ids:
    home_id = team_ids[id][0]
    away_id = team_ids[id][1]

    home_name = team_name[home_id]
    away_name = team_name[away_id]
    print("Liga BBVA game %s - %s" % (home_name, away_name))
    
    select = select_mu % (home_id, away_id)

    cur.execute(select)
    row = cur.fetchone()

    mu1 = row[0]
    mu2 = row[1]

    mu[id] = [mu1, mu2]

    home_reg = outcome(mu1, mu2, 0, 0, "win")
    away_reg = outcome(mu1, mu2, 0, 0, "lose")
    draw_reg = outcome(mu1, mu2, 0, 0, "draw")

    print("%s wins - %.0f%%" % (home_name, home_reg*100))
    print("%s wins - %.0f%%" % (away_name, away_reg*100))
    print("Draw - %.0f%%" % (draw_reg*100))
    print

    string = "%s wins - %.0f%%" % (home_name, home_reg*100) + "\n"
    string += "%s wins - %.0f%%" % (away_name, away_reg*100) + "\n"
    string += "Draw - %.0f%%" % (draw_reg*100)
    
    #print("Tweeting ...")
    #twitter.update_status(status=string)
    #time.sleep(5)

# To test with a local file:
#f = open('live1.js', 'r')
#jsonp = f.read()

# Remove to monitor games

while True:

    time.sleep(30)

    live_json = None
    while live_json is None:
        try:
            live_json = myopener.open(matchlive_url).read()
        except:
            print("Sleeping ...")
            time.sleep(30)
            pass

    #live_json = jsonp[ jsonp.index("(")+1 : jsonp.rindex(")") ]

    live = json.loads(live_json.decode())

    for game in live["matches"]:

        game_id = int(game["id"])

        if (game_id not in ids):
            continue
            
        old_status = status[game_id]
        new_status = game["min"]
        
        if (new_status==old_status):
            continue
    
        r = game["r"]
        s = game["s"]

        home = names[game_id][0]
        away = names[game_id][1]
        mu1 = mu[game_id][0]
        mu2 = mu[game_id][1]

        home_goal = False
        away_goal = False

        if "-" in r:
            home_score = int(r.split("-")[0])
            away_score = int(r.split("-")[1])
            if (home_score > score[game_id][0]):
                string = "%s goal!%s" % (home, hashtag)
                print(string)
                print

                score[game_id][0] = home_score

                home_goal = True
                
                #if Tweet:
                #    print("Tweeting ...")
                #    twitter.update_status(status=string)
                #    time.sleep(5)
                    
            if (away_score > score[game_id][1]):
                string = "%s goal!%s" % (away, hashtag)
                print(string)
                print

                score[game_id][1] = away_score

                away_goal = True
                
                #if Tweet:
                #    print("Tweeting ...")
                #    twitter.update_status(status=string)
                #    time.sleep(5)

            if Tweet and goal_tweet and (home_goal or away_goal):

                status[game_id] = new_status

                stoppage = False
                if "+" in new_status:
                    stoppage = True
                    min = new_status.replace("+","").strip()
                    min = int(min.replace("'",""))
                else:
                    stoppage = False
                    min = int(new_status.replace("'",""))

                home_reg = outcome(mu1, mu2, min, home_score-away_score, "win")
                away_reg = outcome(mu1, mu2, min, home_score-away_score, "lose")
                draw_reg = 1.0 - home_reg - away_reg
            
                hw_string = "%.0f%%" % (home_reg*100)
                aw_string = "%.0f%%" % (away_reg*100)
                dr_string = "%.0f%%" % (draw_reg*100)
        
                string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
                string += "time = " + new_status
            
                string += "\n"


                if (home_p[id] == None):
                    home_delta = 0.00
                    away_delta = 0.00
                else:
                    home_delta = home_reg-home_p[id]
                    away_delta = -home_delta

                if (home_delta>0.0):
                    home_change = " (+%.0f%%)" % (home_delta*100)
                    away_change = " (%.0f%%)" % (away_delta*100)
                elif (home_delta<0.0):
                    home_change = " (%.0f%%)" % (home_delta*100)
                    away_change = " (+%.0f%%)" % (away_delta*100)

                if (home_p[id] == None):
                    string += home + " wins " + hw_string + "\n"
                    string += away + " wins " + aw_string + "\n"
                    string += "Draw " + dr_string
                else:
                    string += home + " wins " + hw_string + home_change + "\n"
                    string += away + " wins " + aw_string + "\n" #+ away_change
                    string += "Draw " + dr_string

                home_p[id] = home_reg

                string += hashtag
                print(string)
                print

                print("Tweeting ...")
                twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
                twitter.update_status(status=string)
                time.sleep(5)
                    
        else:
            continue

        if (new_status == "fifa.half-time"):
            status[game_id] = new_status
        
            min = 45

            home_reg = outcome(mu1, mu2, min, home_score-away_score, "win")
            away_reg = outcome(mu1, mu2, min, home_score-away_score, "lose")
            draw_reg = 1.0 - home_reg - away_reg

            hw_string = "%.0f%%" % (home_reg*100)
            aw_string = "%.0f%%" % (away_reg*100)
            dr_string = "%.0f%%" % (draw_reg*100)
            status[game_id] = new_status
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string = string + "Half-time\n"
            string = string + home + " wins " + hw_string + "\n"
            string = string + away + " wins " + aw_string + "\n"
            string = string + "Draw " + dr_string
            string += hashtag
            print(string)
            print

            if Tweet:
                print("Tweeting ...")
                twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
                twitter.update_status(status=string)
                time.sleep(5)
            
        elif new_status in ("fifa.full-time"):
            
            status[game_id] = new_status
            string =  "%s-%s : %s-%s" % (home,away,home_score,away_score)

            string += "\n"
            
            string = string + "Game is over\n"
            if (home_score>away_score):
                string = string + home + " wins"
            elif (home_score<away_score):
                string = string + away + " wins"
            else:
                string = string + "Draw"

            string += hashtag
            print(string)
            print

            if Tweet:
                print("Tweeting ...")
                twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
                twitter.update_status(status=string)
                time.sleep(5)

        elif "'" in new_status:

            status[game_id] = new_status

            stoppage = False
            if "+" in new_status:
                stoppage = True
                min = new_status.replace("+","").strip()
                min = int(min.replace("'",""))
            else:
                stoppage = False
                min = int(new_status.replace("'",""))

            home_reg = outcome(mu1, mu2, min, home_score-away_score, "win")
            away_reg = outcome(mu1, mu2, min, home_score-away_score, "lose")
            draw_reg = 1.0 - home_reg - away_reg
            
            hw_string = "%.0f%%" % (home_reg*100)
            aw_string = "%.0f%%" % (away_reg*100)
            dr_string = "%.0f%%" % (draw_reg*100)
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string += "time = " + new_status
            
            string += "\n"

            if (home_p[id] == None) or (abs(home_reg-home_p[id])>=tweet_delta):

                if (home_p[id] == None):
                    home_delta = 0.00
                    away_delta = 0.00
                else:
                    home_delta = home_reg-home_p[id]
                    away_delta = -home_delta

                if (home_delta>0.0):
                    home_change = " (+%.0f%%)" % (home_delta*100)
                    away_change = " (%.0f%%)" % (away_delta*100)
                elif (home_delta<0.0):
                    home_change = " (%.0f%%)" % (home_delta*100)
                    away_change = " (+%.0f%%)" % (away_delta*100)

                if (home_p[id] == None):
                    string += home + " wins " + hw_string + "\n"
                    string += away + " wins " + aw_string + "\n"
                    string += "Draw " + dr_string
                else:
                    string += home + " wins " + hw_string + home_change + "\n"
                    string += away + " wins " + aw_string + "\n" #+ away_change
                    string += "Draw " + dr_string

                home_p[id] = home_reg

                string += hashtag
                print(string)
                print

                if Tweet and change_tweet:
                    print("Tweeting ...")
                    twitter = Twython(app_key, app_secret, oauth_token, oauth_token_secret)
                    twitter.update_status(status=string)
                    time.sleep(5)
            else:
                print(string)
                print
                continue
                
        else:
            status[game_id] = new_status
            print(new_status)
            print
