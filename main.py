from itertools import chain
from random import choice

from language_processing import parse, text_to_speech
from tree_patterns import load_pattern_list, TreePatternMatcher, MatchTree

speech = False
silent = True
max_answer_number = 1
speaker = 'google'
whole_sentence = False

bye_phrases = ['Good bye!','auf wiedersehn.','good night','bye bye','it was nice meeting you.',
    'see you soon.','thank you for using knoex.','au revoir']

def answer_question(sent) :

    print "parsing sentence ..."
    trees = parse(sent)

    pattern_list, semantic_translations = load_pattern_list()

    for i,tree in enumerate(trees) :
        tree = tree[0] # cut root node

        png_path = 'temp_tree_' + str(i) + '.png'
        if not silent : 
            print 'saving parse tree as .png ...'
            dot_code = dot_interface.nltk_tree_to_dot(tree)
            dot_interface.dot_to_image(dot_code, 'temp_tree_' + str(i))
            os.popen(conf.image_viewer + ' ' + png_path)

        matcher = TreePatternMatcher()

        match_tree = MatchTree(tree)

        print 'matching patterns ...'
        all_matches = matcher.match_all(match_tree, whole_sentence)
        
        for i,matches in enumerate(all_matches) :
            if silent :
                break
            if matches == [] :
                print 'No matches for', pattern_list[i], '!!'
            for match in matches :
                print 'Match for',[str(node.label()) for node in match],'->',\
                 [str(' '.join(MatchTree.get_terminals(node))) for node in match]

        if not reduce(lambda x,y : x or y,all_matches) :
            no_match = "Could not match any patterns."
            print no_match
            if speech : text_to_speech(no_match,speaker)
            return

        answers = matcher.semantics_all(all_matches)

        answers = list(chain(*answers))

        if len(answers) == 0:
            sorry = "Sorry but I can't find any answers!"
            print sorry
            if speech : text_to_speech(sorry,speaker)
            return

        print answers[0]
        for c in answers[0].split(';') :
            for c2 in c.split('.'):
                if speech : text_to_speech(c2,speaker)

        for i,a in enumerate(answers[1:]) :
            if i+1 == max_answer_number :
                break
            sleep(1)
            if speech : text_to_speech('or',speaker)
            print a
            sleep(1)
            for c in a.split(';') :
                for c2 in c.split('.'):
                    if speech : text_to_speech(c2,speaker)


if __name__ == '__main__':

    while True :
        sent = raw_input('>> ')
        sent = sent.strip()

        if sent == 'exit':
            break

        elif sent.startswith('ner ') :
            sent = sent[4:]
            print ner(sent)

        elif sent.startswith('parse ') :
            pass

        elif sent.startswith('q ') :
            sent = [sent[2:]]
            answers = answer_question(sent)

        elif sent.strip() == 'speech' :
            speech = not speech
            print 'speech toggled', 'on' if speech else 'off'

        elif sent.strip() == 'speaker' :
            speaker = 'google' if speaker=='espeak' else 'espeak'
            print 'speaker toggled to', speaker

        elif sent.strip() == 'silent' :
            silent = not silent
            print 'silent toggled', 'on' if silent else 'off'

        elif sent.startswith('max') :
            try :
                i = int(sent.split()[1])
                max_answer_number = i
                print 'max_answer_number set to', i 
            except :
                print 'wrong max usage!'

        elif sent == 'whole' :
            whole_sentence = not whole_sentence
            print 'whole_sentence toggled', 'on' if whole_sentence else 'off'

        else :
            print 'Well, ... I dont know what to do !'

    bye = choice(bye_phrases)
    print bye
    if speech : text_to_speech(bye, speaker)