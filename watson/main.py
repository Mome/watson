import cmd
from itertools import chain
import os
from random import choice
import string
import sys

import configurations as conf
import dot_interface
from language_processing import parse, text_to_speech
from tree_patterns import load_pattern_list, TreePatternMatcher, MatchTree

class Watson :

    def __init__(self):

        self.speech = True # activates speech synthesis
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
        'thank you for using me.',
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
        trees = parse(sent)

        pattern_list, semantic_translations = load_pattern_list()

        for i,tree in enumerate(trees) :
            tree = tree[0] # cut root node

            if not self.silent :
                print
                print '====================================================='
                print 'Parse Tree:', tree

            # Creates a matchtree (a parsetree with additional properties to match the patterns)
            match_tree = MatchTree(tree)

            if self.silent: print 'matching patterns ...'
            all_matches = self.matcher.match_all(match_tree, self.whole_sentence)
            
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
            if not reduce(lambda x,y : x or y,all_matches) :
                no_match = "Could not match any patterns."
                print no_match
                if self.speech : text_to_speech(no_match,voice)
                return

            # find answers for 
            answers = self.matcher.semantics_all(all_matches)

            # I have no idea
            answers = list(chain(*answers))

            # if no answers have been found stop at this point
            if len(answers) == 0:
                sorry = "Sorry but I can't find any answers!"
                print sorry
                if self.speech : text_to_speech(sorry,voice)
                return

            # print and say answers
            # complicated, ugly stuff to work around some issues with the speech output
            print answers[0]
            for c in answers[0].split(';') :
                for c2 in c.split('.'):
                    if self.speech : text_to_speech(c2,voice)

            for i,a in enumerate(answers[1:]) :
                if i+1 == self.max_answer_number :
                    break
                sleep(1)
                if self.speech : text_to_speech('or',voice)
                print a
                sleep(1)
                for c in a.split(';') :
                    for c2 in c.split('.'):
                        if self.speech : text_to_speech(c2,voice)


class Console(cmd.Cmd):

    def __init__(self, watson):
        cmd.Cmd.__init__(self)
        self.intro = "WATSON-CONSOLE\nAsk me any question:"
        self.prompt = '~> '
        self.watson = watson
        watson.say_hello()

    def emptyline(self) :
        pass

    def default(self, line) :
        self.watson.answer_question(line)

    def do_ner(self, line):
        print 'not yet implemented'

    def do_parse(self,sent):
        trees = parse(sent)
        for i,tree in enumerate(trees) :
            print tree
            png_path = 'temp_tree_' + str(i) + '.png'
            dot_code = dot_interface.nltk_tree_to_dot(tree)
            dot_interface.dot_to_image(dot_code, 'temp_tree_' + str(i))
            os.popen(conf.image_viewer + ' ' + png_path)

    def do_speech(self, line):
        self.watson.toggle_speech()
        print 'speech toggled', 'on' if self.watson.speech else 'off'

    def do_silent(self, line):
        self.watson.toggle_silent()
        print 'silent toggled', 'on' if self.watson.silent else 'off'

    def do_voice(self, line):
        self.watson.next_voice()
        print 'voice switched to', self.watson.voices[self.watson.voice]

    def do_whole(self, line):
        self.watson.toggle_whole_sentence()
        print 'whole_sentence pattern matching toggled', 'on' if self.watson.whole_sentence else 'off'

    def do_max(self,num):
        print num
        try :
            num = int(num)
            self.watson.set_max_answer_number(num)
            print 'max_answer_number set to', self.watson.max_answer_number
        except :
            print 'wrong max usage!'

    def do_hello(self, arg):
        print "hello again", arg, "!"

    def help_hello(self):
        print "syntax: hello [message]",
        print "-- prints a hello message"

    def do_quit(self, arg):
        self.watson.say_good_bye()
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