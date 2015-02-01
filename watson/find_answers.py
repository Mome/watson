from collections import Counter
import os
import string

import nltk

import configurations as conf
import recources
from tree_patterns import TreePatternMatcher, load_pattern_list
import language_processing as nlp

def document_search_wrapper(topics, filter_words, ner_types) :
    answer_candidates = document_search(topics, filter_words, ner_types)
    return select_best_answer(answer_candidates)


def document_search(topics, filter_words, ner_types):

    if filter_words in [str,unicode] :
        filter_words = [filter_words]
    if ner_types in [str,unicode] :
        ner_types = [ner_types]

    print 'get articles from wikipedia'
    articles = recources.get_corpus(topics)

    # merge to one string
    text = unicode('\n'.join(articles))

    # filter non ascii characters (might not be a problem with python3)
    text = filter(lambda x: x in string.printable, text)

    print len(text), 'characters in text'

    # split into paragraphs and paragraphs into list of words
    paragraphs = nlp.tokenize(text,'pw')
    print 'number of paragraphs', len(paragraphs)

    print 'translate abbreviations and slang ...'
    paragraphs = [nlp.canonicalize(p) for p in paragraphs]

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
    
    good_sentences = nlp.tokenize(" ".join(good_paragraphs))[0]

    print 'perform a named entity recognition'
    tagged_sentences = nlp.ner_tag(good_sentences)

    tagged_text = [item for sublist in tagged_sentences for item in sublist]

    # prints ner tags
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