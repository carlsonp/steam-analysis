import string, re, sys, random
from pymongo import MongoClient
from nltk.corpus import stopwords # pip3 install nltk
from nltk.stem.wordnet import WordNetLemmatizer
import gensim # pip3 install gensim
from gensim import corpora
import pyLDAvis.gensim # pip3 install pyLDAvis, IPython
import config # config.py
# python3
# >>> import nltk
# >>> nltk.download('popular')


# https://www.analyticsvidhya.com/blog/2016/08/beginners-guide-to-topic-modeling-in-python/
# https://towardsdatascience.com/topic-modelling-in-python-with-nltk-and-gensim-4ef03213cd21
# https://github.com/bmabey/pyLDAvis
# https://miningthedetails.com/blog/python/lda/GensimLDA/


client = MongoClient(host=config.mongodb_ip, port=config.mongodb_port)
db = client['steam']
collection = db['apps']

ret = collection.find({"updated_date": {"$exists": True}, "type": {"$in": ["game", "dlc"]}},
                        {"detailed_description":1})
descriptions = []
for v in ret:
    descriptions.append(v['detailed_description'])

random.shuffle(descriptions) #in-place
# take a subset
descriptions = descriptions[:100]

stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()

def clean(doc):
    # strip HTML tags
    # order of string operations matters here!
    html_cleaned = re.compile(r'<[^<]+?>').sub('', doc)
    stop_free = " ".join([i for i in html_cleaned.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())

    return normalized

doc_clean = [clean(doc).split() for doc in descriptions]
dictionary = corpora.Dictionary(doc_clean)

# create document term matrix
doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

#lda = gensim.models.ldamodel.LdaModel # single-threaded
lda = gensim.models.ldamulticore.LdaMulticore # multi-threaded
ldamodel = lda(doc_term_matrix, num_topics=50, id2word=dictionary, passes=100)

lda_display = pyLDAvis.gensim.prepare(ldamodel, doc_term_matrix, dictionary, sort_topics=False)
pyLDAvis.save_html(lda_display, "pyldavis.html")
