#!/usr/bin/env ruby

require "csv"
require "mechanize"

agent = Mechanize.new{ |agent| agent.history.max_size=0 }
agent.user_agent = 'Mozilla/5.0'

base = "http://www.baseball-reference.com/teams"

game_xpath = '//table[@id="team_schedule"]/tbody/tr'

games = CSV.open("csv/games.csv","w")

header = ["year", "team_id", "rk", "game_number", "date", "boxscore_url",
          "team", "home_away", "opponent",
          "win_loss", "runs_scored", "runs_allowed", "innings",
          "win_loss_record", "rank", "gb", "win_pitcher", "loss_pitcher",
          "save_pitcher", "time", "day_night", "attendance", "streak"]

games << header

CSV.foreach("csv/teams.csv", headers:true) do |team|

  year = team["year"]
  team_id = team["team_id"]

  url = "#{base}/#{team_id}/#{year}-schedule-scores.shtml"
  print "Pulling #{year}-#{team_id}\n"

  begin
    page = agent.get(url)
  rescue
    retry
  end

  page.parser.xpath(game_xpath).each do |r|

    row = [year, team_id]
    
    r.xpath("td").each do |e|
      row << e.text.strip
    end

#    if (row[1]=="LgAvg")
#      next
#    end

    games << row

  end

end

games.close

