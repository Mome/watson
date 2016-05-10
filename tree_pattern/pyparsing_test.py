from pyparsing import *
import xml.etree.ElementTree as ET


constitunt_makros = {
    'V' : 'VB VBD VBG VBN VBP VBZ'.split(),
    'N' : 'NN NNS NNP NNPS'.split(),
    'W' : 'WHADJP WHAVP WHNP WHPP'.split(),
}

constituents = 'S SBAR SBARQ SINV SQ ADJP ADVP CONJP FRAG INTJ LST NAC NP NX PP PRN PRT QP RRC UCP VP WHADJP WHAVP WHNP WHPP X CC CD DT EX FW IN JJ JJR JJS LS MD NN NNS NNP NNPS PDT POS PRP PRP$ RB RBR RBS RP SYM TO UH VB VBD VBG VBN VBP VBZ WDT WP WP$ WRB'


constraint = Group(Word(alphanums).setResultsName('key') + Suppress('=') + Word(alphanums).setResultsName('value')).setResultsName('constraint')
constraint_list = Suppress('[') + constraint + ZeroOrMore(Suppress(',') + constraint)  + Suppress(']')
p_token = Group(Word(alphas).setResultsName('alpha') + Optional(Word(nums)).setResultsName('num') + Optional(constraint_list)).setResultsName('token')

pattern = Group(ZeroOrMore(p_token)).setResultsName('pattern')
rule = Group(p_token.setResultsName('head') + Suppress('::') + pattern).setResultsName('rule')
#rule = rule.setResultsName('code')
rule.ignore( pythonStyleComment )

# test grammar


#with open('test.pattern') as f:
#    result = code.parseString(f.read())


#code_string = code_string.strip() + '\n'

#result = code.parseString(code_string)

string = """
NP :: VP1[a=r, bla=gna] X[r=w]
S :: SS SA HH
"""

rules = []
trees = []
for line in string.splitlines():
    line = line.strip()
    if not line: 
        continue
    result = rule.parseString(line)
    xml_code = result.asXML()
    tree = ET.fromstring(xml_code)
    rules.append(result.rule)
    trees.append(tree)



