from pyparsing import *
import xml.etree.ElementTree as ET


constitunt_makros = {
    'V' : 'VB VBD VBG VBN VBP VBZ'.split(),
    'N' : 'NN NNS NNP NNPS'.split(),
    'W' : 'WHADJP WHAVP WHNP WHPP'.split(),
}

constituents = 'S SBAR SBARQ SINV SQ ADJP ADVP CONJP FRAG INTJ LST NAC NP NX PP PRN PRT QP RRC UCP VP WHADJP WHAVP WHNP WHPP X CC CD DT EX FW IN JJ JJR JJS LS MD NN NNS NNP NNPS PDT POS PRP PRP$ RB RBR RBS RP SYM TO UH VB VBD VBG VBN VBP VBZ WDT WP WP$ WRB'

singel_constraint_value = Word(alphanums).setResultsName('value')
constraint_value = Group(
                    singel_constraint_value |
                    Suppress('{')
                        + singel_constraint_value
                        + ZeroOrMore(Suppress(',') + singel_constraint_value)
                        + Suppress('}')
                ).setResultsName('value_set')

constraint = Group(
                Word(alphanums).setResultsName('key')
                + Suppress('=')
                + constraint_value
            ).setResultsName('constraint')

constraint_list = Group(
                    Suppress('[')
                    + constraint
                    + ZeroOrMore(Suppress(',') + constraint)
                    + Suppress(']')
                ).setResultsName('constraints_list')

p_token = Group(
            Word(alphas).setResultsName('alpha')
            + Optional(Word(nums)).setResultsName('num')
            + Optional(constraint_list)
        ).setResultsName('token')

pattern = Group(ZeroOrMore(p_token)).setResultsName('pattern')

arg = Word(alphanums).setResultsName('arg')
arguments = Group(arg + ZeroOrMore(Suppress(',') + arg)).setResultsName('arglist')
predicate = Word(alphanums).setResultsName('name') + Suppress('(') + Optional(arguments) + Suppress(')')
predicate_list = Group(Optional(predicate + ZeroOrMore(',' + predicate))).setResultsName('predicate_list')

rule = Group(p_token.setResultsName('head') + Suppress('::') + pattern + Optional(Suppress('::') + predicate_list)).setResultsName('rule')
#rule = rule.setResultsName('code')
rule.ignore( pythonStyleComment )

# test grammar


#with open('test.pattern') as f:
#    result = code.parseString(f.read())


#code_string = code_string.strip() + '\n'

#result = code.parseString(code_string)

string = """
S :: SS1[a=b, c={2,34}] SA HH2 :: a(p1, p2)
"""

#NP :: VP1[a=r, bla=gna] X[r=w]
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
    print(result.rule.asXML())


