# Club Soccer Twitter Bot

Live tweets soccer match win probability using FIFA's API.

This assumes my soccer database is installed, including all of the club analytics and PostgreSQL extensions. bot.py is Python 2; bot3.py is Python 3.

Setting 'Tweet = False' allows testing without actually tweeting.
If 'goal_tweet = True' it'll tweet updates when goals are scored.
If 'tweet_delta = True' it'll tweet updates when the home team's win probability changes by more than 'tweet_delta'.



You'll need a .twitter file in your home directory containing keys obtained from Twitter. This has the form:
```
{
"app_key" : "APP_KEY",
"app_secret" : "APP_SECRET",
"oauth_token" : "OAUTH_TOKEN",
"oauth_token_secret" : "OATH_TOKEN_SECRET"
}
```
