from collections import Counter
import os
import string
from time imporcreatt sleep

import nltk

import dot_interface
import configurations as conf
from recources import get_wikipedia_text
from tree_patterns import TreePatternMatcher, MatchTree, load_pattern_list
from language_processing import text_to_speech, ner, canonicalize, tokenize, ner_tagger


def document_search(topic, filter_words, ner_types):
    print 'get articles from wikipedia'
    articles = get_wikipedia_text(topic,lang='en',summary=False)
    articles += get_wikipedia_text(topic,lang='simple',summary=False)

    # merge to one string
    articles = unicode('\n'.join(articles))

    # filter non ascii characters (might not be a problem with python3)
    articles = filter(lambda x: x in string.printable, articles)

    print 'len articles:',len(articles)

    # split in paragraphs
    paragraphs = articles.split('\n')

    print 'tokenize into words'
    paragraphs = [nltk.word_tokenize(p) for p in paragraphs]

    # paragraphs = tokenize(articles,'pw') # use my own more generic method

    print 'translate abbreviations and slang ...'
    paragraphs = [canonicalize(p) for p in paragraphs]

    print 'check each paragraph if it contains a keyword'
    good_paragraphs = []
    for p in paragraphs :
        for fw in filter_words :
            if fw.lower() in [lp.lower() for lp in p] :
                good_paragraphs += [p]
                break

    print 'len good_paragraphs', len(good_paragraphs)
    if len(good_paragraphs) == 0 :
        print 'no paragraphs found'
        return

    # flatten list of keyword list
    good_paragraphs = [item for sublist in good_paragraphs for item in sublist]
    
    good_sentences = tokenize(" ".join(good_paragraphs))

    print 'perform a named entity recognition'
    tagged_sentences = ner_tagger.tag_sents(good_sentences)

    tagged_text = [item for sublist in tagged_sentences for item in sublist]

    print set(zip(*tagged_text)[1])

    solutions = {}
    for word, tag in tagged_text:
        if tag not in ner_types :
            continue
        if tag in solutions :
            solutions[tag] += [word]
        else :
            solutions[tag] = [word]

    return solutions.items()


def select_best_answer(options):
    output = []
    for opt in options :
        counts = Counter(opt[1])
        m = max(counts.values())
        best = []
        for key in counts :
            if counts[key] == m :
                best.append(key)
        output.append((opt[0],best))
    return output