from itertools import chain, islice, tee, takewhile, dropwhile
import nltk
from collections import namedtuple
import os
from nltk.parse import stanford
import logging
from pprint import pformat, pprint
from pyparsing import *
#logging.basicConfig(level=logging.INFO)


stanford_path = os.path.expanduser('~/.local/stanford-parser-full-2015-12-09')
os.environ['STANFORD_MODELS'] = stanford_path
os.environ['STANFORD_PARSER'] = stanford_path
stanford_parser = stanford.StanfordParser() 

constitunt_makros = {
    'V' : 'VB VBD VBG VBN VBP VBZ'.split(),
    'N' : 'NN NNS NNP NNPS'.split(),
    'W' : 'WHADJP WHAVP WHNP WHPP'.split(),
}

constituent_list = """S SBAR SBARQ SINV SQ ADJP ADVP CONJP FRAG INTJ LST NAC NP
NX PP PRN PRT QP RRC UCP VP WHADJP WHAVP WHNP WHPP X CC CD DT EX FW IN JJ JJR
JJS LS MD NN NNS NNP NNPS PDT POS PRP PRP$ RB RBR RBS RP SYM TO UH VB VBD VBG
VBN VBP VBZ WDT WP WP$ WRB""".split()


class RuleParser:

    PatternToken = namedtuple('PatternToken',['varname','constraints'])
    Rule = namedtuple('Rule', ['head', 'pattern', 'predicates'])


    def __init__(self):
        nonums = alphas + '.!?$'
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
            Word(nonums).setResultsName('alpha')
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

        self._parser = rule


    def parse_rules(self, rules_str):
        parser = self._parser

        rules = []
        for line in rules_str.splitlines():
            line = line.strip()
            if not line:
                continue
            parsetree = parser.parseString(line).rule
            head = self.__class__._construct_ptoken(parsetree.head)
            pattern = [self.__class__._construct_ptoken(pt) for pt in parsetree.pattern]
            predicates = [self.__class__._construct_predicate(pre) for pre in parsetree.predicate_list]
            rules.append(self.__class__.Rule(head, pattern, None))
        return rules


    @classmethod
    def _construct_ptoken(cls, ptoken):
        constraint_dict = {}
        if ptoken.alpha in constituent_list:
            constraint_dict['label'] = {ptoken.alpha}
        elif not ptoken.alpha.isupper():
            constraint_dict['terminal'] = {ptoken.alpha}

        for key, value_set in ptoken.constraints_list:
            value_set = set(value_set)
            if key in constraint_dict:
                constraint_dict[key].update(value_set)
            else:
               constraint_dict[key] = value_set
        return cls.PatternToken(ptoken.alpha + ptoken.num, constraint_dict)

    @classmethod
    def _construct_predicate(cls, predicate):
        print('pred',type(predicate), predicate)
        #print('pname', predicate.name)
        #print('plist', predicate.arglist)




def add_properties(prop_tree):
    for node in prop_tree.descendant_or_self():
        node.properties['terminal'] = node.terminals


class PatternMatcher:

    Match = namedtuple('Match', ['sent', 'rule','head_match','pattern_match'])

    def __init__(self, rules, whole=True, head_only_ones=True):
        self.rules = rules
        self.whole = whole
        self.head_only_ones = head_only_ones


    def match(self, sents):
        """Constructs PropertyTrees from text and passes to match_rules"""

        if isinstance(sents, str):
            sents = [
                nltk.word_tokenize(s)
                for s in nltk.sent_tokenize(sents)
            ]

        logging.info('Construnct parsetree for all sentences!')
        parse_trees = stanford_parser.parse_sents(sents)

        for pt, sent in zip(parse_trees, sents):

            pt = list(pt)[0][0] # convert to list get tree and remove root node
            
            pt.draw()
            logging.debug('ParseTree:' + pformat(pt))

            logging.info('Construct property trees from parsetrees!')
            prop_tree = PropertyTree.from_parsetree(pt)
            add_properties(prop_tree)
            logging.debug(str(prop_tree))

            for rule, head_match, pattern_match in self.match_rules(prop_tree):
                yield PatternMatcher.Match(sent, rule, head_match, pattern_match)


    def match_rules(self, prop_tree):

        if self.head_only_ones:
            matched_nodes = [] # list of roots that have already been matched

        for rule in self.rules:

            head, pattern, predicates = rule

            for node in prop_tree.descendant_or_self():

                satisfies_constaints = node.has_properties(**head.constraints)

                logging.debug(
                    'HEAD_TRY:\n Constraints: %s\n Properties: %s\n> %s!'
                    %(str(head.constraints), str(node.properties),
                        'YES!' if satisfies_constaints else 'NO!'))

                if not satisfies_constaints:
                    continue
                if self.head_only_ones and node in matched_nodes:
                    continue
                
                if self.whole:
                    start_nodes = node.no_preceding()
                else:
                    start_nodes = node.descendant_or_self()
                
                for match in self._search(start_nodes, pattern):

                    yield rule, (head.varname, node), match

                    if self.head_only_ones:
                        matched_nodes.append(node)
                        break


    def _search(self, nodes, pattern, match=None, index=0):

        if match is None:
            match = [None]*len(pattern)

        varname, constraints = pattern[index]

        for node in nodes:

            satisfies_constaints = node.has_properties(**constraints)

            logging.debug(
                    'PATTERN_TRY:%i\n Constraints: %s\n Properties: %s\n> %s!'
                    %(index, str(constraints), str(node.properties),
                        'YES!' if satisfies_constaints else 'NO!'))

            if not satisfies_constaints:
                continue

            match[index] = (varname, node) # assign node to variable

            imidiate_following = node.imidiate_following(root=node)

            if len(pattern) == index+1:
                if self.whole:
                    imidiate_following = list(imidiate_following)
                    
                if self.whole and len(imidiate_following):
                    logging.debug('Match, but not whole.')
                else:
                    logging.debug('Pattern matched!!!')
                    yield tuple(match)
            else:
                yield from self._search(imidiate_following, pattern, match, index+1)


    @classmethod
    def from_str(cls, rules_str):
        parser = RuleParser()
        rules = parser.parse_rules(rules_str)
        return cls(rules)



class IteratorTree:
    def __init__(self, parent=None, children=None):
        self.children = []
        if children: self.add_children(*children)
        self.parent = parent

    def add_children(self, *children):
        for child in children: child.parent=self
        self.children += children

    def ancestor(self, root=None):
        if not (self is root):
            parent = self.parent
            while not (parent is root):
                if parent is None:
                    raise IteratorTree.RootNotFoundError()
                yield parent
                parent = parent.parent
            if root: yield root
            
    def ancestor_or_self(self, root=None):
        yield self
        yield from self.ancestor(root)

    def descendant(self):
        #return chain.from_iterable(
        #    child.descendant_or_self for child in self.children)
        return islice(self.descendant_or_self(), 1, None)

    def descendant_or_self(self):
        yield self
        for child in self.children:
            for des in child.descendant_or_self():
                yield des

    def sibling(self):
        yield from filter(self.__ne__, self.sibling_or_self())

    def sibling_or_self(self):
        if self.parent: yield from self.parent.children

    def following(self):
        for ancestor in self.ancestor_or_self():
            for fosib in ancestor.following_sibling():
                for follower in fosib.descendant_or_self():
                    yield follower

    def following_sibling(self):
        yield from islice(
            dropwhile(self.__ne__, self.sibling_or_self()), 1, None)

    def preceding(self):
        for ancestor in self.ancestor_or_self():
            for fosib in ancestor.preceding_sibling():
                yield from fosib.descendant_or_self()

    def preceding_sibling(self):
        yield from takewhile(self.__ne__, self.sibling_or_self())

    def imidiate_following(self, root=None):

        def next_sibling(node):
            if node.parent and node.parent.children:
                i = node.parent.children.index(node)
                if len(node.parent.children) > i+1:
                    return node.parent.children[i+1]

        # find next sibling of ancestor or self
        for node in self.ancestor_or_self(root):
            next = next_sibling(node)
            if next:
                yield from next.no_preceding() # node and all firstborn
                break

    def no_preceding(self):
        yield self
        node = self
        while node.children:
            node = node.children[0]
            yield node

    def __str__(self):
        name = self.__class__.__name__
        if len(self.children)==0:
            return name
        inner = ' '.join(str(c) for c in self.children)        
        return ''.join([name, '[ ', inner, ']'])

    class RootNotFoundError(Exception):
        pass
            



class PropertyTree(IteratorTree):

    def __init__(self, parent=None, children=None, **keyargs):
        super(PropertyTree, self).__init__(parent, children)
        self.properties = keyargs
        self.small_world = True # everything unknown is false

        # add IteratorTree as properties
        for prop in IteratorTree.__dict__:
            ... # ???

    def __getitem__(self, key):
        return self.properties[key]



    @classmethod
    def from_parsetree(cls, nltktree, parent=None):
        if isinstance(nltktree, str):
            parent.properties['terminal'] = nltktree
            new_tree = None
        else:
            new_tree = PropertyTree(label=nltktree.label(), parent=parent)
            new_tree.children = [cls.from_parsetree(subtree, new_tree) for subtree in nltktree]
            new_tree.children = [x for x in new_tree.children if not x is None]
        return new_tree


    @property
    def terminals(self):
        if 'terminal' in self.properties:
            out = self.properties['terminal']
        else:
            out = ' '.join(c.terminals for c in self.children)
        return out


    def has_properties(self, **props):

        for key, value_set in props.items():
            if not (key in self.properties):
                if self.small_world:
                    break
                else:
                    continue

            if callable(self.properties[key]):
                self.properties[key] = self.properties[key]()

            if self.properties[key] not in value_set:
                break
        else:
            return True

        return False


    def __repr__(self):
        return self.__str__()
        

    def __str__(self):
        name = self.properties.get('label', self.__class__.__name__)
        if len(self.children)==0:
            return name + ' "' + self.terminals + '"'
        inner = ' '.join(str(c) for c in self.children)        
        return ''.join([name, '[ ', inner, ']'])


Predicate = namedtuple('Predicate', ['name','args'])


def construct_predicate(self, head_match, pattern_match, predicate_rules):
    varnames, nodes = zip(head_match, *pattern_match)
    print(type(varnames))
    print(type(nodes))

    


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    rules = """
    S :: NP VP :: VP(NP).
    NP :: DT NN
    """
    # NP :: DT NN
    # 
    # S :: DT NN is NP
    # S :: DT NN VP

    sent = "Bob saw John with his eyes."

    matcher = PatternMatcher.from_str(rules)

    print()
    for match in matcher.match(sent):
        sent, rule, head_match, pattern_match = match

        hm_varname,  hm_node  = head_match
        pm_varnames, pm_nodes = zip(*pattern_match)

        hm_label = hm_node['label']
        pm_labels = [n['label'] for n in pm_nodes]

        hm_term = hm_node['terminal']
        pm_terms = [n['terminal'] for n in pm_nodes]

        print()
        print(sent)
        print(' ', hm_varname, '\t|\t', '\t'.join(pm_varnames))
        print(' ', hm_label, '\t|\t', '\t'.join(pm_labels))
        print()
        print(hm_label, '▶', hm_term)
        for L,T in zip(pm_labels, pm_terms):
            print(L, '▶', T)

        input()
