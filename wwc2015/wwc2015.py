#!/usr/bin/env python

from twython import Twython
from scipy.stats import skellam
from urllib import FancyURLopener

import psycopg2
import json
import time
import os

# True - prints to screen and tweets
# False - only prints to screen

Tweet = False

# FIFA's hidden API

matchlive_url = "http://lup.fifa.com/live/common/competitions/womensworldcup/_feed/_listmachlive.js"

# Need to pull from database

ot_ft = 0.36821584388673

# Stoppage stop assumptions
# Generally want these to be conservative

stoppage_1reg = 2
stoppage_2reg = 4

stoppage_1ot = 1
stoppage_2ot = 1

hashtag = "\n\n#FIFAWWC"

def overtime(mu1, mu2, min, up, outcome):

# Sloppy

    if (min < 90):
        aup = 0
        amin = 90
    else:
        aup = up
        amin = min
    
    if (amin <= 105): # 1st extra time
        time_r = (120.0-amin)+stoppage_1ot+stoppage_2ot
    elif (amin <= 120): # 2nd extra time
        time_r = (120.0-amin)+stoppage_2ot

    ft = time_r/(30.0+stoppage_1ot+stoppage_2ot)

    if (outcome=="draw"):
        p = skellam.pmf(-aup, ft*mu1*ot_ft, ft*mu2*ot_ft)
    elif (outcome == "lose"):
        p = skellam.cdf(-1-aup, ft*mu1*ot_ft, ft*mu2*ot_ft)
    else:
        p = skellam.cdf(-1+aup, ft*mu2*ot_ft, ft*mu1*ot_ft)

    return(p)

def outcome(mu1, mu2, min, up, outcome):

# Sloppy

    if (min > 90):
        if (outcome=="draw"):
            p = 1.0
        else:
            p = 0.0
        return(p)

    if (min <= 45): # 1st half
        time_r = (90.0-min)+stoppage_1reg+stoppage_2reg
    elif (min <= 90): # 2nd half
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

ids = [300269493,300269496]

names = {}
names[300269493] = ["#England", "#Canada"]
names[300269496] = ["#Australia", "#Japan"]

team_name = {}
team_name["aus"] = "Australia"
team_name["can"] = "Canada"
team_name["chn"] = "China"
team_name["fra"] = "France"
team_name["ger"] = "Germany"
team_name["usa"] = "USA"
team_name["eng"] = "England"
team_name["jpn"] = "Japan"

team_ids = {}
team_ids[300269493] = ["eng", "can"]
team_ids[300269496] = ["aus", "jpn"]

# Possibly for future use

fields = {}
fields[300269493] = "neutral"
fields[300269496] = "neutral"

score = {}
score[300269493] = [0, 0]
score[300269496] = [0, 0]

status = {}
status[300269493] = "fifa.full-time"
status[300269496] = "fifa.full-time"
status[300269493] = ""
status[300269496] = ""

home_p = {}
home_p[300269493] = None
home_p[300269496] = None

# Possible status
# Match starting time (local)
# "fifa.lineups"
# "fifa.end1sthalf"
# "fifa.end2ndhalf"
# "result"

select_mu = "select * from fifa.mu where team_id='%s' and opponent_id='%s'"

mu = {}

print

for id in ids:
    home_id = team_ids[id][0]
    away_id = team_ids[id][1]
    home_name = team_name[home_id]
    away_name = team_name[away_id]
    print "Women's World Cup game %s - %s" % (home_name, away_name)
    
    select = select_mu % (home_id, away_id)

    cur.execute(select)
    row = cur.fetchone()

    mu1 = row[4]
    mu2 = row[5]

    mu[id] = [mu1, mu2]

    home_reg = outcome(mu1, mu2, 0, 0, "win")
    away_reg = outcome(mu1, mu2, 0, 0, "lose")
    draw_reg = outcome(mu1, mu2, 0, 0, "draw")
    home_ot = overtime(mu1, mu2, 90, 0, "win")
    away_ot = overtime(mu1, mu2, 90, 0, "lose")
    draw_ot = overtime(mu1, mu2, 90, 0, "draw")
    home_win = home_reg + draw_reg*(home_ot + 0.5*draw_ot)
    away_win = 1.0 - home_win
    print "%s wins - %.1f%%" % (home_name, home_win*100)
    print "%s wins - %.1f%%" % (away_name, away_win*100)
    print

# To test with a local file:
#f = open('live1.js', 'r')
#jsonp = f.read()

# Remove to monitor games

while True:

    #time.sleep(15)

    jsonp = None
    while jsonp is None:
        try:
            jsonp = myopener.open(matchlive_url).read()
        except:
            print "Sleeping ..."
            time.sleep(15)
            pass

    live_json = jsonp[ jsonp.index("(")+1 : jsonp.rindex(")") ]

    live = json.loads(live_json)

    for game in live["matches"]:

        game_id = int(game["id"])
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

        if "-" in r:
            home_score = int(r.split("-")[0])
            away_score = int(r.split("-")[1])
            if (home_score > score[game_id][0]):
                string = "%s goal!%s" % (home, hashtag)
                print string
                print
                
                if Tweet:
                    print "Tweeting ..."
                    twitter.update_status(status=string)
                    time.sleep(5)
                    
            if (away_score > score[game_id][1]):
                string = "%s goal!%s" % (away, hashtag)
                print string
                print
                
                if Tweet:
                    print "Tweeting ..."
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

            home_ot = overtime(mu1, mu2, min, home_score-away_score, "win")
            away_ot = overtime(mu1, mu2, min, home_score-away_score, "lose")
            draw_ot = 1.0 - home_ot - away_ot

            home_win = home_reg + draw_reg*(home_ot + 0.5*draw_ot)
            away_win = 1.0 - home_win

            hw_string = "%.1f%%" % (home_win*100)
            aw_string = "%.1f%%" % (away_win*100)
            status[game_id] = new_status
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string = string + "Half-time\n"
            string = string + home + " wins " + hw_string + "\n"
            string = string + away + " wins " + aw_string
            string += hashtag
            print string
            print

            if Tweet:
                print "Tweeting ..."
                twitter.update_status(status=string)
                time.sleep(5)

        elif new_status in ("fifa.endfirstextra"):

            status[game_id] = new_status
        
            min = 105
            home_reg = outcome(mu1, mu2, min, home_score-away_score, "win")
            away_reg = outcome(mu1, mu2, min, home_score-away_score, "lose")
            draw_reg = 1.0 - home_reg - away_reg

            home_ot = overtime(mu1, mu2, min, home_score-away_score, "win")
            away_ot = overtime(mu1, mu2, min, home_score-away_score, "lose")
            draw_ot = 1.0 - home_ot - away_ot

            home_win = home_reg + draw_reg*(home_ot + 0.5*draw_ot)
            away_win = 1.0 - home_win

            hw_string = "%.1f%%" % (home_win*100)
            aw_string = "%.1f%%" % (away_win*100)
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string = string + "End of 1st extra\n"
            string = string + home + " wins " + hw_string + "\n"
            string = string + away + " wins " + aw_string
            string += hashtag
            print string
            print

            if Tweet:
                print "Tweeting ..."
                twitter.update_status(status=string)
                time.sleep(5)

        elif new_status in ("fifa.endsecondextra"):

            status[game_id] = new_status
        
            home_win = 0.5
            away_win = 0.5

            hw_string = "%.1f%%" % (home_win*100)
            aw_string = "%.1f%%" % (away_win*100)
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string = string + "Entering penalty kicks\n"
            string = string + home + " wins " + hw_string + "\n"
            string = string + away + " wins " + aw_string
            string += hashtag
            print string
            print

            if Tweet:
                print "Tweeting ..."
                twitter.update_status(status=string)
                time.sleep(5)

        elif new_status in ("fifa.penaltiesphase"):

            status[game_id] = new_status
        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string = string + "Entering penalty kicks\n"
            string = string + home + " wins " + hw_string + "\n"
            string = string + away + " wins " + aw_string
            string += hashtag
            print string
            print

            if Tweet:
                print "Tweeting ..."
                twitter.update_status(status=string)
                time.sleep(5)
            
        elif new_status in ("fifa.end2ndhalf"):
            
            status[game_id] = new_status
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            
            if (home_score==away_score):
                string = string + "Entering overtime\n"
                string += hashtag
                print string
                print

                if Tweet:
                    print "Tweeting ..."
                    twitter.update_status(status=string)
                    time.sleep(5)

        elif new_status in ("fifa.full-time"):
            
            status[game_id] = new_status
            string =  "%s-%s : %s-%s" % (home,away,home_score,away_score)

            scorepenh = game["scorepenh"]
            scorepena = game["scorepena"]

            if (scorepenh<>""):
                string += " ("+scorepenh+"-"+scorepena+")\n"
            else:
                string += "\n"
            
            string = string + "Game is over\n"
            if (home_score>away_score):
                string = string + home + " wins"
            elif (home_score<away_score):
                string = string + away + " wins"
            else:
                scorepenh = game["scorepenh"]
                scorepena = game["scorepena"]
                if (scorepenh>scorepena):
                    string = string + home + " wins"
                else:
                    string = string + away + " wins"

            string += hashtag
            print string
            print

            if Tweet:
                print "Tweeting ..."
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
            
            home_ot = overtime(mu1, mu2, min, home_score-away_score, "win")
            away_ot = overtime(mu1, mu2, min, home_score-away_score, "lose")
            draw_ot = 1.0 - home_ot - away_ot
            
            home_win = home_reg + draw_reg*(home_ot + 0.5*draw_ot)
            away_win = 1.0 - home_win

            hw_string = "%.1f%%" % (home_win*100)
            aw_string = "%.1f%%" % (away_win*100)

        
            string =  "%s-%s : %s-%s\n" % (home,away,home_score,away_score)
            string += "time = " + new_status
            
            string += "\n"

            if (home_p[id] == None) or (abs(home_win-home_p[id])>=0.01):

                if (home_p[id] == None):
                    home_delta = 0.00
                    away_delta = 0.00
                else:
                    home_delta = home_win-home_p[id]
                    away_delta = -home_delta

                if (home_delta>0.0):
                    home_change = " (+%.1f%%)" % (home_delta*100)
                    away_change = " (%.1f%%)" % (away_delta*100)
                elif (home_delta<0.0):
                    home_change = " (%.1f%%)" % (home_delta*100)
                    away_change = " (+%.1f%%)" % (away_delta*100)

                if (home_p[id] == None):
                    string += home + " wins " + hw_string + "\n"
                    string += away + " wins " + aw_string
                else:
                    string += home + " wins " + hw_string + home_change + "\n"
                    string += away + " wins " + aw_string + away_change

                home_p[id] = home_win

                string += hashtag
                print string
                print

                if Tweet:
                    print "Tweeting ..."
                    twitter.update_status(status=string)
                    time.sleep(5)
            else:
                print string
                print
                continue
                
        else:
            status[game_id] = new_status
            print new_status
            print
