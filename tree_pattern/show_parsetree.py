import nltk, os, sys
from nltk.parse import stanford


stanford_path = os.path.expanduser('~/.local/stanford-parser-full-2015-12-09')
os.environ['STANFORD_MODELS'] = stanford_path
os.environ['STANFORD_PARSER'] = stanford_path
stanford_parser = stanford.StanfordParser()


sents = " ".join(sys.argv[1:])

sents = [
    nltk.word_tokenize(s)
    for s in nltk.sent_tokenize(sents)
]

parse_trees = stanford_parser.parse_sents(sents)

for pt, sent in zip(parse_trees, sents):
	pt = list(pt)[0][0]
	pt.draw()