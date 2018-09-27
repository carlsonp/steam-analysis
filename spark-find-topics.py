import sys
from pyspark import SparkContext # pip3 install pyspark
from pyspark.mllib.clustering import LDA, LDAModel
from pyspark.mllib.linalg import Vectors
from pymongo import MongoClient
import config

# Adapted from:
# https://github.com/apache/spark/blob/master/examples/src/main/python/mllib/latent_dirichlet_allocation_example.py


client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
db = client['steam']
collection = db['apps']

sc = SparkContext(master="spark://192.168.1.171:7077", appName="SteamFindTopicsLDA")


# Load and parse the data
ret = collection.find({"updated_date": {"$exists": True}, "type": {"$in": ["game", "dlc"]}},
                        {"detailed_description":1})#.limit(500)
descriptions = []
for v in ret:
    descriptions.append(v['detailed_description'])


data = sc.parallelize(descriptions)

parsedData = data.map(lambda line: Vectors.dense([float(x) for x in line.strip().split(' ')]))
# Index documents with unique IDs
corpus = parsedData.zipWithIndex().map(lambda x: [x[1], x[0]]).cache()

# Cluster the documents into k topics using LDA
ldaModel = LDA.train(corpus, k=50, maxIterations=100)

# Output topics. Each is a distribution over words (matching word count vectors)
print("Learned topics (as distributions over vocab of " + str(ldaModel.vocabSize())
      + " words):")
topics = ldaModel.topicsMatrix()
for topic in range(3):
    print("Topic " + str(topic) + ":")
    for word in range(0, ldaModel.vocabSize()):
        print(" " + str(topics[word][topic]))

# Save and load model
ldaModel.save(sc, "/data/spark-model")
sameModel = LDAModel\
    .load(sc, "/data/spark-model")

sc.stop()
