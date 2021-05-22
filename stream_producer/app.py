from kafka import KafkaProducer
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API
import os, json

api_key = "YOUR_TWITTER_API_KEY"
api_secret_key = "YOUR_TWITTER_API_SECRET_KEY"
access_token = "YOUR_TWITTER_ACCESS_TOKEN"
access_token_secret = "YOUR_TWITTER_ACCESS_TOKEN_SECRET"

# authorize the API Key
auth = OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_token_secret)

KAFKA_BROKER_URL = os.environ.get('KAFKA_BROKER_URL')
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER_URL)

class StdOutListener(StreamListener):
    def on_status(self, data):
        producer.send("streaming.tweets", data.text.encode('utf-8'))
        return True
    
    def on_error(self, status_code):
        if status_code == 420:
            return False

api = API(auth)
india_trends = api.trends_place(23424848, exclude= 'hashtags')
trends = []
for value in india_trends:
    for trend in value['trends']:
        trends.append(trend['name'])

l = StdOutListener()
stream = Stream(auth, l)
stream.filter(track=trends)
