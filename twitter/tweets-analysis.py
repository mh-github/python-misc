from __future__ import division
import sys, csv, nltk, re, string, heapq, gensim
from nltk.corpus   import stopwords
from nltk.tokenize import TweetTokenizer
from collections   import Counter
from prettytable   import PrettyTable
from textblob      import TextBlob
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from sklearn.cluster import KMeans
from gensim import corpora, models
from nltk.stem.wordnet import WordNetLemmatizer

sw            = stopwords.words('english')
lemma         = WordNetLemmatizer()

def fetchTweetsFromFile(twitter_handle):
    fields = []
    rows   = []

    with open(twitter_handle + '.csv', 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';')

        # This skips the first row of the CSV file.
        # https://evanhahn.com/python-skip-header-csv-reader/
        next(csvreader)

        for row in csvreader:
            rows.append(row)
        print "Total no. of tweets: {}".format(csvreader.line_num-2)

    return rows

def clean_text_and_tokenize(line):
    line   = re.sub(r'\$\w*', '', line)  # Remove tickers
    line   = re.sub(r'http?:.*$', '', line)
    line   = re.sub(r'https?:.*$', '', line)
    line   = re.sub(r'pic?.*\/\w*', '', line)
    line   = re.sub(r'[' + string.punctuation + ']+', ' ', line)  # Remove puncutations like 's
    
    tokens = TweetTokenizer(strip_handles=True, reduce_len=True).tokenize(line)
    tokens = [w.lower() for w in tokens if w not in sw and len(w) > 2 and w.isalpha()]
    tokens = [lemma.lemmatize(word) for word in tokens]
    
    return tokens

def getCleanedWords(lines):
    words = []
    
    for line in lines:
        words += clean_text_and_tokenize(line)
    return words

def lexical_diversity(tokens):
    return 1.0 * len(set(tokens)) / len(tokens)

# Helper function for computing number of words per tweet
def average_words(lines):
    total_words = sum([len(s.split()) for s in lines])
    return 1.0 * total_words / len(lines)

def top_words(words, top=5):
    pt = PrettyTable(field_names=['Words', 'Count'])
    c = Counter(words)
    [pt.add_row(kv) for kv in c.most_common()[:top]]
    pt.align['Words'], pt.align['Count'] = 'l', 'r'  # Set column alignment
    print pt

def popular_tweets(tweet_rows, top=5):
    popular = []
    for row in tweet_rows:
        if len(row) >= 8:
            popular.append([row[8], int(row[2])+int(row[3]), row[4], row[9]])
    topTweets = heapq.nlargest(
        top, popular, key=lambda e: e[1])  # ref sof -> 2243542

    print "\nPrinting top {} tweets".format(top)
    counter = 0
    for (id, popularity, tweet, url) in topTweets:
        counter += 1
        print "{}. {}".format(counter, tweet)
        print "Popularity = {}".format(popularity)
        print "Link = {}".format(url)
        print "-------------------"

def clean_tweet(tweet):
    return " ".join(clean_text_and_tokenize(tweet))

def sentiment_analysis_basic(tweets):
    positive_tweets = 0
    neutral_tweets  = 0
    negative_tweets = 0

    for tweet in tweets:
        analysis  = TextBlob(tweet)
        sentiment = analysis.sentiment.polarity

        if sentiment > 0:
            positive_tweets += 1
        elif sentiment == 0:
            neutral_tweets += 1
        else:
            negative_tweets += 1
    total_tweets_analysed      = positive_tweets + neutral_tweets + negative_tweets
    positive_tweets_percentage = positive_tweets / total_tweets_analysed * 100
    neutral_tweets_percentage  = neutral_tweets  / total_tweets_analysed * 100

    print "\nNo. of positive tweets = {} Percentage = {}".format(
        positive_tweets, positive_tweets_percentage)
    print "No. of neutral tweets  = {} Percentage = {}".format(
        neutral_tweets, neutral_tweets_percentage)
    print "No. of negative tweets = {} Percentage = {}".format(
        negative_tweets, 100 - (positive_tweets_percentage + neutral_tweets_percentage))

# sof -> 20078816
def remove_non_ascii(text):
    return ''.join(i for i in text if ord(i) < 128)

def clusterTweetsKmeans(tweets):
    taggeddocs   = []
    tag2tweetmap = {}
    for index, i in enumerate(tweets):
        if len(i) > 2:  # Non empty tweets
            tag = u'SENT_{:d}'.format(index)
            sentence = TaggedDocument(
                words=gensim.utils.to_unicode(i).split(), tags=[tag])
            tag2tweetmap[tag] = i
            taggeddocs.append(sentence)

    model = Doc2Vec(
        taggeddocs, dm=0, alpha=0.025, size=20, min_alpha=0.025, min_count=0)
    print " "
    for epoch in range(60):
        model.train(
            taggeddocs, total_examples=model.corpus_count, epochs=model.iter)
        model.alpha -= 0.002  # decrease the learning rate
        model.min_alpha = model.alpha  # fix the learning rate, no decay

    dataSet = model.docvecs.doctag_syn0  # this works, thanks a lot sof -> 43476869
    kmeansClustering = KMeans(n_clusters=5)
    centroidIndx = kmeansClustering.fit_predict(dataSet)
    topic2wordsmap = {}
    for i, val in enumerate(dataSet):
        tag = model.docvecs.index_to_doctag(i)
        topic = centroidIndx[i]
        if topic in topic2wordsmap.keys():
            for w in (tag2tweetmap[tag].split()):
                topic2wordsmap[topic].append(w)
        else:
            topic2wordsmap[topic] = []
    for i in topic2wordsmap:
        print("Topic {} has words: {}".format(i + 1, ' '.join(remove_non_ascii(word) for word in topic2wordsmap[i][:10])))

def main():
    twitter_handle = sys.argv[1]
    tweet_rows     = fetchTweetsFromFile(twitter_handle)

    tweets = [row[4] for row in tweet_rows]
    print "Average Number of words per tweet = {}".format(average_words(tweets))
    words = getCleanedWords(tweets)
    print "Lexical diversity = {}".format(lexical_diversity(words))
    
    top_words(words)
    popular_tweets(tweet_rows)

    cleaned_tweets = []
    for tweet in tweets:
        cleaned_tweets.append(clean_tweet(tweet))    
    sentiment_analysis_basic(cleaned_tweets)
    clusterTweetsKmeans(cleaned_tweets)

if __name__ == '__main__':
    main()
