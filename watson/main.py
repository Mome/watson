import cmd
from random import choice
import sys
from pattern.en import parsetree

import configurations as conf
import draw_graph
from language_processing import parse, text_to_speech, ner_tag
from tree_patterns import load_pattern_list, TreePatternMatcher, MatchTree
from find_answers import document_search_wrapper

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
        sentences = parsetree(sent, relations=True, )

        if len(sentences) > 1:
            print "Only processing one sentence at a time"
            return

        sentence = sentences[0]
        if not self.silent:
            print
            print "Subject: ", sentence.relations["SBJ"]
            print "Object: ", sentence.relations["OBJ"]
            print "(Verb: ", sentence.relations["VP"], ")"
            print "Prepositional NP: ", sentence.pnp

        if sentence.relations["SBJ"]:
            print("Subject of sentence is not a question word but",
                  sentence.relations["SBJ"][1].string)
            return

        # We boldly assume only one object and only on PNP in our easy question

        pnp = sentence.pnp[0]
        #get rid of prepositions and articles (first word is preposition)
        topic = ""
        for word in pnp.words[1:]:
            if "NP" in word.type:
                topic += (word.string + " ")

        obj = sentence.relations["OBJ"][1]
        obj_words = obj.words
        if obj_words[0].type == "DT":
            obj_words = obj.words[1:]
        keywords = []
        for word in obj_words:
            keywords.append(word.string)

        if not self.silent:
            print
            print "topic: ", topic
            print "keyword: ", keywords

        answers = document_search_wrapper(topic, keywords, [])

        for answer in answers:
            print answer
            if self.speech:
                text_to_speech(answer, voice)

        # use stanford parser to create parsetrees (multiple parsetrees for multiple sentences)
        # TODO: parse only handles single sentences. Split into sentences.
        #trees = parse(sent)

        #pattern_list, semantic_translations = load_pattern_list()

        #for i,tree in enumerate(trees) :
            #tree = tree[0] # cut root node

            ## print text representation of parsetree
            #if not self.silent :
                #print
                #print '====================================================='
                #print 'Parse Tree:', tree

            #if self.silent: print 'matching patterns ...'
            ## try to match patterns of file pattern_list in parsetree of sentence
            #all_matches = self.matcher.match_all(tree, self.whole_sentence)
            
            ## print matches of parsetree
            #if not self.silent :
                #print
                #for i,matches in enumerate(all_matches) :
                    #if matches == [] :
                        #print 'No matches for', pattern_list[i], '!!'
                    #for match in matches :
                        #print 'Match for',[str(node.label()) for node in match],'->',\
                         #[str(' '.join(MatchTree.get_terminals(node))) for node in match]
                #print '====================================================='
                #print

            ## if there are no matches stop at this point
            #if not reduce(lambda x,y : x or y, all_matches) :
                #no_match = "Could not match any patterns."
                #print no_match
                #if self.speech : text_to_speech(no_match,voice)
                #return

            ## assigns a function call to each match
            ## i.e.: looks for answers to the question
            ## this is still messy and might need an own class
            #answers = self.matcher.semantics_all(all_matches)

            ## flattens the answers to a list of answers

            #answers = list(chain(*answers))

            ## if no answers have been found stop at this point
            #if len(answers) == 0:
                #sorry = "Sorry but I can't find any answers!"
                #print sorry
                #if self.speech : text_to_speech(sorry,voice)
                #return

            ## reduce number of answers
            #answers = answers[:min(len(answers), self.max_answer_number)]

            #for answer in answers :
                #print answer
                #if self.speech : text_to_speech(answer, voice)


class Console(cmd.Cmd):

    def __init__(self, watson):
        cmd.Cmd.__init__(self)
        self.intro = "WATSON-CONSOLE\nAsk me any question:"
        self.prompt = '~> '
        self.watson = watson
        self.draw_parsetree_engine = 'nltk'
        watson.say_hello()

    def emptyline(self) :
        pass

    def default(self, line) :
        self.watson.answer_question(line)

    def do_ner(self, sent):
        tagged_sent = ner_tag(sent)
        print
        for ts in tagged_sent :
            print ts[0] + '\t' + ts[1]
        print

    def do_parse(self,sent):
        trees = parse(sent)
       
        for i,tree in enumerate(trees) :
            print tree
            if self.draw_parsetree_engine :
                draw_graph.draw_parsetree(tree, self.draw_parsetree_engine, i)

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

    def help_max(self):
        print "syntax: max $NUMBER",
        print "-- sets the number of maximal answers to $NUMBER"

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
