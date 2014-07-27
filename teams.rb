#!/usr/bin/env ruby
# coding: utf-8

bad = " "

require "csv"
require "mechanize"

agent = Mechanize.new{ |agent| agent.history.max_size=0 }
agent.user_agent = 'Mozilla/5.0'

base = "http://www.baseball-reference.com/leagues/MLB"

team_xpath = '//*[@id="teams_standard_batting"]/tbody[1]/tr'

teams = CSV.open("csv/teams.csv","w")

header = ["year", "team_id", "batting_players", "batting_age", "runs_per_game",
          "g", "pa", "ab", "r", "h", "d", "t", "hr", "rbi", "sb", "cs", "bb",
          "so", "ba", "obp", "slg", "ops", "ops_plus", "tb", "gdp", "hbp",
          "sh", "sf", "ibb", "lob"]

teams << header

(1988..2014).each do |year|

  url = "#{base}/#{year}.shtml"
  print "Pulling #{year}\n"

  begin
    page = agent.get(url)
  rescue
    retry
  end

  page.parser.xpath(team_xpath).each do |r|
    
    row = [year]
    r.xpath("td").each_with_index do |e,i|
      row << e.text
    end

    if (row[1]=="LgAvg")
      next
    end

    teams << row

  end

end

teams.close

