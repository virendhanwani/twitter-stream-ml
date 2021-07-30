from kafka import KafkaConsumer, KafkaProducer
import os, json
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import numpy as np
from scipy.special import softmax
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from pymongo import MongoClient

app = Flask(__name__)
socketio = SocketIO(app)
client = MongoClient('mongodb://root:example@mongo:27017/')
dbs = client.list_database_names()
tweetsdb = client['tweetsdb']
joytweets = tweetsdb['joytweets']
angrytweets = tweetsdb['angrytweets']
sadtweets = tweetsdb['sadtweets']
optimismtweets = tweetsdb['optimismtweets']


KAFKA_BROKER_URL = os.environ.get("KAFKA_BROKER_URL")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")
ANGER_TOPIC = os.environ.get("ANGER_TOPIC")
JOY_TOPIC = os.environ.get("JOY_TOPIC")
OPTIMISM_TOPIC = os.environ.get("OPTIMISM_TOPIC")
SADNESS_TOPIC = os.environ.get("SADNESS_TOPIC")

def preprocess(text):
    new_text = []
    for t in text.split(" "):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return " ".join(new_text)

MODEL = "cardiffnlp/twitter-roberta-base-emotion"
tokenizer = AutoTokenizer.from_pretrained('tokenizer')
model = TFAutoModelForSequenceClassification.from_pretrained('tfmodel')

@app.route('/')
def home():
    return send_from_directory('/usr/app', 'index.html')

@socketio.on('connect', namespace='/kafka')
def test_connect():
    emit('logs', {'data': 'Connection Established'})


@socketio.on('kafkaconsumer', namespace='/kafka')
def kafkaconsumer():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers= KAFKA_BROKER_URL,
        value_deserializer= lambda value: json.loads(value),
    )
    producer = KafkaProducer(
        bootstrap_servers= KAFKA_BROKER_URL,
        value_serializer = lambda value: json.dumps(value).encode()
    )

    for message in consumer:
        transaction: dict = message.value
        text = preprocess(transaction['text'])
        emit('kafkaconsumer', {'data': text})
        encoded_input = tokenizer(text, return_tensors='tf')
        output = model(encoded_input)
        scores = output[0][0].numpy()
        scores = softmax(scores)
        ranking = np.argsort(scores)
        ranking = ranking[::-1]
        if ranking[0] == 0:
            producer.send(ANGER_TOPIC, transaction)
            angrytweets.insert_one(transaction)
            emit('angryproducer', {'data': text})
        elif ranking[0] == 1:
            producer.send(JOY_TOPIC, transaction)
            joytweets.insert_one(transaction)
            emit('joyproducer', {'data': text})
        elif ranking[0] == 2:
            producer.send(OPTIMISM_TOPIC, transaction)
            optimismtweets.insert_one(transaction)
            emit('optimismproducer', {'data': text})
        else:
            producer.send(SADNESS_TOPIC, transaction)
            sadtweets.insert_one(transaction)
            emit('sadproducer', {'data': text})



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)