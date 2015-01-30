from os import popen, devnull
from string import punctuation
from subprocess import call, PIPE

import nltk
from nltk.parse.stanford import StanfordParser
from nltk.tag.stanford import NERTagger, POSTagger

import configurations as conf


def parse(text, normalize=True) :
    """Parses string, iterable of strings or nested iterables of strings"""

    # saves stanford_parser as global variable,
    # such that it is not created everytime parse is executed
    if not 'stanford_parser' in globals():
        global stanford_parser
        stanford_parser = StanfordParser(conf.stanford_parser,conf.stanford_models)
    
    if hasattr(text, '__iter__') :
        return [parse(t) for t in text]
    else :
        if normalize : text = canonicalize(text)
        trees = stanford_parser.raw_parse(text)
    return trees


def pos_tag(sent, tagger='stanford'):
    
    # saves pos_tagger as global variable,
    # such that it is not created everytime pos_tag is executed
    if not 'pos_tagger' in globals():
        global pos_tagger
        pos_tagger = POSTagger(conf.stanford_pos_model, path_to_jar=conf.stanford_postagger, encoding='UTF-8')

    if tagger == 'nltk' :
        tokens = tokenize(sent, 's')
        return nltk.pos_tag(tokens)
    elif tagger == 'stanford' :
        tokens = tokenize(sent)
        return pos_tagger.tag(tokens)
    else :
        raise ValueError('No such tagger: ' + tagger)


def named_entity_recognition(sent, silent=True) :

    # saves ner_tagger as global variable,
    # such that it is not created everytime named_entity_recognition is executed
    if not 'ner_tagger' in globals():
        global ner_tagger
        ner_tagger = NERTagger(conf.stanford_ner_classifier, conf.stanford_ner)

    if type(sent) in [str,unicode]:
        sent = nltk.word_tokenize(sent)
    tagged = ner_tagger.tag(sent)
    if not silent :
        print 'ner-tags:',tagged
    return tagged


def tokenize(text_structure, types='psw'):
    """ splits a text into list of paragrpahs
        a paragraph is represented by a list of sentences
        a sentence is representerd by a list of words and puctuation """

    #--> maybe 'text tilling' algorithm to split into multi-paragraph subtopics

    # split into paragraphs
    if 'p' in types :
        text_structure = _paragraph_tokenize(text_structure)

    # split into sentences
    if 's' in types :
        text_structure = _sent_tokenize(text_structure)

    # word tokenization
    if 'w' in types :
        text_structure = _word_tokenize(text_structure)

    return text_structure


def text_to_speech(text, engine='google'):

    if engine == 'google' :
        text = text.replace('(',' ')
        text = text.replace(')',' ')
        text = text.replace('`','')
        text = text.replace("'",'')
        text = text.replace("-",' ')

        # call the speech.sh bash-script with text
        cmd = conf.watson_path + conf.sep + 'speech.sh ' + '"' + text + '"'
        FNULL = open(devnull, 'w') # used to suppress error messages from mplayer
        call(cmd.split(), stderr=FNULL)

    elif engine == 'espeak' :
        cmd = 'espeak ' + '"' + text + '"'
        call(cmd.split())

    else :
        print 'No such speech engine:', engine


def _paragraph_tokenize(text_structure):
    if hasattr(text_structure, '__iter__') :
        text_structure = [paragraph_tokenize(substructure) for substructure in text_structure]
    else :
        # split into paragraphs
        text_structure = text_structure.split('\n')
        # remove leading and trailing whitespace characters of each paragraph
        text_structure = [sts.strip() for sts in text_structure]
        # remove empty paragraphs
        text_structure = [sts for sts in text_structure if sts!='']
    return text_structure


def _sent_tokenize(text_structure):
    if hasattr(text_structure, '__iter__') :
        text_structure = [sent_tokenize(substructure) for substructure in text_structure]
    else :
        text_structure = nltk.sent_tokenize(text_structure)
    return text_structure


def _word_tokenize(text_structure):
    if hasattr(text_structure, '__iter__') :
        text_structure = [word_tokenize(substructure) for substructure in text_structure]
    else :
        text_structure = nltk.word_tokenize(text_structure)
    return text_structure


def untokenize(tokens) :
    """ transforms an arbitrarily deep list of list of words
        into a string, so basically reverses the tokenization process """
    if tokens and hasattr(tokens[0], '__iter__') :
        return [untokenize(t) for t in tokens]
    return "".join([" "+i if not i.startswith("'") and i not in punctuation else i for i in tokens]).strip()


def canonicalize(words):

    if type(words) in [str, unicode] :
        words = words.strip().split()
        was_string = True
    else :
        was_string = False

    for i,word in enumerate(words) :
        if word in _transform_dict :
            words[i] = _transform_dict[word]
            print word
        elif word in _abbreviations :
            words[i] = _abbreviations[word]
            print word
    #flatten list : [item for sublist in l for item in sublist]
    if was_string :
        return untokenize(words)
    else :
        return words


_transform_dict = {
    
    "I'm" : "I am",
    "he's" : "he is",
    "He's" : "He is",
    "she's" : "she is",
    "She's" : "She is",
    "it's" : "it is",
    "It's" : "It is",
    "that's" : "that is",
    "That's" : "That is",
    "there's" : "there is",
    "There's" : "There is",
    "What's" : "what is",
    "what's" : "what is",
    "Whats" : "What is",
    "whats" : "what is",
    "Where's" : "where is",
    "where's" : "where is",
    "I'll" : "I will",
    "Ill" : "I will",
    "you'll" : "you will",
    "You'll" : "You will", 
    "they're" : "they are",
    "They're" : "they are",
    "you're" : "you are",
    "You're" : "you are",
    "we're" : "we are",
    "We're" : "we are",
    "has't" : "has not",
    "doesn't" : "does not",
    "won't" : "will not",
    "was't" : "was not",
    "is't" : "is not",
    "don't" : "do not",
    "can't" : "can not",
    "cannot" : "can not",
    "could't" : "could not",
    "would't" : "would not",
    "wanna" : "want to",
    "gonna" : "going to"
}

_abbreviations = {
    'U.S.A.' : 'USA'
}


# needs some improvement
def transform_arithmetics(expr):
    
    def is_number(num) :
        try :
            float(num)
            return True
        except :
            return False

    tokens = tokenize(expr)
    for i,token in enumerate(tokens) :
        if token in _arithmetic_dict :
            tokens[i] = _arithmetic_dict[token]
        elif is_number(token) :
            tokens[i] = token
        else :
            return False
    return " ".join(tokens)

_arithmetic_dict = {
    'zero' : '0',
    'one' : '1',
    'two' : '2',
    'three' : '3',
    'four' : '4',
    'five' : '5',
    'six' : '6',
    'seven' : '7',
    'eight' : '8',
    'nine' : '9',
    'ten' : '10',
    'eleven' : '11',
    'twelve' : '12',
    'and' : '+',
    'minus' : '-',
    'plus' : '+',
    'times' : '*',
    '**' : '**',
    '-' : '-',
    '+' : '+',
    '*' : '*',
    '^' : '**',
    '/' : '/' 
}

ner = named_entity_recognition

"""def flatten(nested_list):
    for i,item in enumerate(nested_list):
        if hasattr(item, '__iter__') :
            flatten"""