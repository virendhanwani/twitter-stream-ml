from kafka import KafkaProducer
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler, Stream, API
import os, json, time

api_key = "YOUR_TWITTER_API_KEY"
api_secret_key = "YOUR_TWITTER_API_SECRET_KEY"
access_token = "YOUR_TWITTER_ACCESS_TOKEN"
access_token_secret = "YOUR_TWITTER_ACCESS_TOKEN_SECRET"

# authorize the API Key
auth = OAuthHandler(api_key, api_secret_key)
auth.set_access_token(access_token, access_token_secret)

KAFKA_BROKER_URL = os.environ.get('KAFKA_BROKER_URL')
KAFKA_TOPIC = os.environ.get('KAFKA_TOPIC')
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer= lambda value: json.dumps(value).encode())

class StdOutListener(StreamListener):
    tweet_counter = 0
    max_tweets = 10000

    def on_status(self, data):
        transaction: dict = {'text': data.text, 'source': data.source}
        producer.send(KAFKA_TOPIC, transaction)
        StdOutListener.tweet_counter += 1
        if StdOutListener.tweet_counter < StdOutListener.max_tweets:
            return True
        else:
            producer.flush()
            time.sleep(10)
            producer.close(5)
            return False
    
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
