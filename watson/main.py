#! /usr/bin/python
import cmd
from itertools import chain
import os
from random import choice
import readline
import string
import sys

import configurations as conf
import draw_graph
from language_processing import parse, text_to_speech, ner_tag
from tree_patterns import load_pattern_list, TreePatternMatcher, MatchTree

class Watson :

    def __init__(self):

        self.speech = False # activates speech synthesis
        self.silent = True # additional output for question processing
        self.max_answer_number = 1 
        self.voice = 0
        self.whole_sentence = False # if true patterns also match parts of sentences
        self.voices = ['google','espeak']
        self.matcher = TreePatternMatcher()

        self.greetings = ['Hello',
        'Good Morning, sir. What a wonderful day. How can I help you?']

        self.bye_phrases = ['Good bye!',
        'auf wiedersehn.',
        'good night',
        'bye bye',
        'it was nice meeting you.',
        'see you soon.', 
        'au revoir']

    def toggle_speech(self) :
        self.speech = not self.speech

    def toggle_silent(self) :
        self.silent = not self.silent

    def toggle_whole_sentence(self):
        self.whole_sentence = not self.whole_sentence

    def next_voice(self) :
        self.voice = (self.voice+1)%len(self.voices)

    def set_max_answer_number(self, num) :
        self.max_answer_number = num

    def say_hello(self):
        greeting = choice(self.greetings)
        voice = self.voices[self.voice]
        if self.speech : text_to_speech(greeting, voice)

    def say_good_bye(self):
        bye = choice(self.bye_phrases)
        print bye
        voice = self.voices[self.voice]
        if self.speech : text_to_speech(bye, voice)

    def answer_question(self,sent) :

        voice = self.voices[self.voice]

        print "parsing sentence ..."
        # use stanford parser to create parsetrees (multiple parsetrees for multiple sentences)
        # TODO: parse only handles single sentences. Split into sentences.
        trees = parse(sent)

        pattern_list, semantic_translations = load_pattern_list()

        for i,tree in enumerate(trees) :
            tree = tree[0] # cut root node

            # print text representation of parsetree
            if not self.silent :
                print
                print '====================================================='
                print 'Parse Tree:', tree

            if self.silent: print 'matching patterns ...'
            # try to match patterns of file pattern_list in parsetree of sentence
            all_matches = self.matcher.match_all(tree, self.whole_sentence)
            
            # print matches of parsetree
            if not self.silent :
                print
                for i,matches in enumerate(all_matches) :
                    if matches == [] :
                        print 'No matches for', pattern_list[i], '!!'
                    for match in matches :
                        print 'Match for',[str(node.label()) for node in match],'->',\
                         [str(' '.join(MatchTree.get_terminals(node))) for node in match]
                print '====================================================='
                print

            # if there are no matches stop at this point
            if not reduce(lambda x,y : x or y, all_matches) :
                no_match = "Could not match any patterns."
                print no_match
                if self.speech : text_to_speech(no_match,voice)
                return

            # assigns a function call to each match
            # i.e.: looks for answers to the question
            # this is still messy and might need an own class
            answers = self.matcher.semantics_all(all_matches)

            # flattens the answers to a list of answers

            answers = list(chain(*answers))

            # if no answers have been found stop at this point
            if len(answers) == 0:
                sorry = "Sorry but I can't find any answers!"
                print sorry
                if self.speech : text_to_speech(sorry,voice)
                return

            # reduce number of answers
            answers = answers[:min(len(answers), self.max_answer_number)]

            for answer in answers :
                print answer
                if self.speech : text_to_speech(answer, voice)


class Console(cmd.Cmd):

    def __init__(self, watson):
        cmd.Cmd.__init__(self)
        self.intro = "WATSON-CONSOLE\nAsk me any question:"
        self.prompt = (unichr(0x25B6) + u' ').encode('utf-8')
        self.watson = watson
        self.draw_parsetree_engine = 'nltk'
        self.display = True
        self.load_history()
        watson.say_hello()

    def load_history(self):
        path = conf.cmd_hist_path
        if os.path.exists(path) :
            readline.read_history_file(path)

    def save_history(self):
        path = conf.cmd_hist_path
        #import readline # ?? why ??
        readline.write_history_file(path)

    def emptyline(self) :
        pass

    def default(self, line) :
        self.watson.answer_question(line)

    def do_ner(self, sent):
        """prints named entity relation tags for a sentence"""
        tagged_sent = ner_tag(sent)
        print
        for ts in tagged_sent :
            print ts[0] + '\t' + ts[1]
        print

    def do_parse(self,sent):
        """print parstree of a sentence"""
        trees = parse(sent)
       
        for i,tree in enumerate(trees) :
            tree = tree[0] # cut root node
            print tree
            if self.display :
                draw_graph.draw_parsetree(tree, self.draw_parsetree_engine, i)

    def do_display(self, line):
        """ turns on/off all features that require a GUI """
        self.display = not self.display
        print 'display toggled', 'on' if self.display else 'off'

    def do_speech(self, line):
        self.watson.toggle_speech()
        print 'speech toggled', 'on' if self.watson.speech else 'off'

    def do_silent(self, line):
        """toggles detailed output on/off"""
        self.watson.toggle_silent()
        print 'silent toggled', 'on' if self.watson.silent else 'off'

    def do_voice(self, line):
        self.watson.next_voice()
        print 'voice switched to', self.watson.voices[self.watson.voice]

    def do_whole(self, line):
        """if toggled on: the pattern matching must fit the whole sentence"""
        self.watson.toggle_whole_sentence()
        print 'whole_sentence pattern matching toggled', 'on' if self.watson.whole_sentence else 'off'

    def do_draw(self, line):
        """switches parsetree draw engine"""
        engine = self.draw_parsetree_engine
        engine = 'graphviz' if engine=='nltk' else 'nltk'
        print 'parsetree draw engine switched to', engine
        self.draw_parsetree_engine = engine

    def do_max(self,num):
        print num
        try :
            num = int(num)
            self.watson.set_max_answer_number(num)
            print 'max_answer_number set to', self.watson.max_answer_number
        except :
            print 'wrong max usage!'

    def help_max(self):
        print "syntax: max $NUMBER",
        print "-- sets the number of maximal answers to $NUMBER"

    def do_quit(self, arg):
        self.watson.say_good_bye()
        self.save_history()
        sys.exit(1)

    def help_quit(self):
        print "syntax: quit",
        print "-- terminates the application"

    # shortcuts
    do_q = do_quit
    do_exit = do_quit


def main():
    watson = Watson()
    console = Console(watson)
    console.cmdloop()

if __name__ == '__main__':
    main()
