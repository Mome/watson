from os.path import abspath, dirname, sep

# sep is the os dependent path seperator

watson_path = dirname(abspath(__file__))

up = sep + '..' + sep

# STANFORD PARSER
stanford_path = abspath(watson_path + up + 'stanford-parser-full')
stanford_parser = stanford_path + sep + 'stanford-parser.jar'
stanford_models = stanford_path + sep + 'stanford-parser-3.4.1-models.jar'

# STANFORD NAMED ENTITY TAGGER
stanford_ner_path = abspath(watson_path + up + 'stanford-ner')
stanford_ner_classifier = stanford_ner_path + sep + 'classifiers' + sep + 'english.all.3class.distsim.crf.ser.gz'
#stanford_ner_classifier = stanford_ner_path + sep + 'classifiers' + sep + 'english.muc.7class.distsim.crf.ser.gz'
stanford_ner = stanford_ner_path + sep + 'stanford-ner.jar'

# STANFORD PART OF SPEECH TAGGER
stanford_pos_path = abspath(watson_path + up + 'stanford-postagger')
stanford_pos_model = stanford_pos_path + sep + 'models' + sep + 'english-bidirectional-distsim.tagger'
stanford_postagger = stanford_pos_path + sep +'stanford-postagger.jar'

# MISCELLANEOUS
cmd_hist_path = watson_path + sep + '.console_history'
tree_patterns_path =  watson_path + sep + 'pattern_list'
pattern_semantic_separator = '->'
image_viewer = 'gnome-open'


del abspath, dirname
