from numpy.core.fromnumeric import prod
from kafka import KafkaConsumer, KafkaProducer
import os, json
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TFAutoModelForSequenceClassification
import numpy as np
from scipy.special import softmax
# from scipy.special import softmax

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
tokenizer = AutoTokenizer.from_pretrained(MODEL)

model = TFAutoModelForSequenceClassification.from_pretrained(MODEL)  

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
    encoded_input = tokenizer(text, return_tensors='tf')
    output = model(encoded_input)
    scores = output[0][0].numpy()
    scores = softmax(scores)
    ranking = np.argsort(scores)
    ranking = ranking[::-1]
    if ranking[0] == 0:
        producer.send(ANGER_TOPIC, transaction)
    elif ranking[0] == 1:
        producer.send(JOY_TOPIC, transaction)
    elif ranking[0] == 2:
        producer.send(OPTIMISM_TOPIC, transaction)
    else:
        producer.send(SADNESS_TOPIC, transaction)