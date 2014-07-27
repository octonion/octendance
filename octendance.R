library(twitteR)
library(stringr)

games <- read.csv(file="csv/games.csv",header=TRUE)

games <- games[games$home_away == "" & !(games$date==""), ]

games <- games[games$year >= 2010, ]

games$attendance = as.numeric(games$attendance)
games$year = as.factor(games$year)

date <- str_split(games$date, " ")

games$dow <- sapply(date, "[", 1)
games$month <- sapply(date, "[", 2)
games$day <- sapply(date, "[", 3)

#games <- games[!games$month == "Nov", ]

upcoming <- games[games$year =="2014" & games$date == "Saturday, Jul 26", ]
#upcoming$day_night <- "N"

games <- games[games$attendance >= 1000, ]
games$la = log(games$attendance)

head(games)

model <- attendance ~ team*(year+opponent+month+dow)

out <- lm(model, games)

summary(out)

upcoming
estimate <- predict(out, upcoming, interval = "confidence")

g <- data.frame(date = upcoming$date, team = upcoming$team,
                opponent = upcoming$opponent)
g <- cbind(g, estimate)

g

#load("twitCred.RData")
#registerTwitterOAuth(twitCred)

l = g[1,]
s1 <- "MLB attendance projection bot."
s2 <- paste(l$date, "-", l$team, "vs", l$opponent, sep = " ")
s3 <- paste("Projection =", round(l$fit),
              ", Lower =", round(l$lwr),
              ", Upper =", round(l$upr), sep = " ")
test <- paste(s1, s2, s3, sep = "\n")

#tweet(test)
cat(test)
