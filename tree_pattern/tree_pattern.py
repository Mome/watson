from itertools import chain, islice, tee, takewhile, dropwhile, count
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

constituent_macros = {
    'V'  : 'VB VBD VBG VBN VBP VBZ'.split(),
    'N'  : 'NN NNS NNP NNPS'.split(),
    'W'  : 'WHADJP WHAVP WHNP WHPP'.split(),
    'SS' : 'S SBAR SBARQ SINV SQ'.split(),
    'J'  : 'JJ JJR JJS'.split(),
}

constituent_list = """S SBAR SBARQ SINV SQ ADJP ADVP CONJP FRAG INTJ LST NAC NP
NX PP PRN PRT QP RRC UCP VP WHADJP WHAVP WHNP WHPP X CC CD DT EX FW IN JJ JJR
JJS LS MD NN NNS NNP NNPS PDT POS PRP PRP$ RB RBR RBS RP SYM TO UH VB VBD VBG
VBN VBP VBZ WDT WP WP$ WRB""".split()

relation_constituents = constituent_macros['V'] + ['IN', 'VP', 'TO']
statement_contsituents = constituent_macros['SS'] + constituent_macros['W']

def contsituen2type(const):
    if const in relation_constituents:
        return 'relation'
    if const in statement_contsituents:
        return 'statement'


class RuleParser:

    PatternToken = namedtuple('PatternToken',['varname','constraints'])
    Rule = namedtuple('Rule', ['head', 'pattern', 'relations', 'transformation'])


    def __init__(self):
        nonums = alphas + '.!?$_§@'
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

        #arg = Word(alphanums).setResultsName('arg')
        #arguments = Group(arg + ZeroOrMore(Suppress(',') + arg)).setResultsName('arglist')
        #predicate = Word(alphanums).setResultsName('name') + Suppress('(') + Optional(arguments) + Suppress(')')
        #predicate_list = Group(Optional(predicate + ZeroOrMore(',' + predicate))).setResultsName('predicate_list')

        relation = Group(
            Word(nonums + nums).setResultsName('left')
            + Suppress(oneOf('-> -'))
            + Word(nonums + nums).setResultsName('right')
            ).setResultsName('relation')
        relation_list = Group(relation + ZeroOrMore(Suppress(',') + relation)).setResultsName('relation_list')

        transformation = Word(nonums + nums).setResultsName('transformation')

        rule = Group(
            p_token.setResultsName('head')
            + Suppress(':')
            + pattern
            + Suppress(':')
            + Optional(relation_list)
            + Suppress(':')
            + Optional(transformation)
        ).setResultsName('rule')
        
        rule.ignore( pythonStyleComment )

        self._parser = rule


    def parse_rules(self, rules_str):
        parser = self._parser

        rules = []
        for line in rules_str.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parsetree = parser.parseString(line).rule
            head = self.__class__._construct_ptoken(parsetree.head)
            pattern = [self.__class__._construct_ptoken(pt) for pt in parsetree.pattern]
            relations = [(left, right) for left, right in parsetree.relation_list]
            transformation = parsetree.transformation
            rules.append(self.__class__.Rule(head, pattern, relations, transformation))
        return rules


    @classmethod
    def _construct_ptoken(cls, ptoken):
        constraint_dict = {}
        if ptoken.alpha in constituent_list:
            constraint_dict['label'] = {ptoken.alpha}
        elif ptoken.alpha in constituent_macros:
            labels = constituent_macros[ptoken.alpha]
            constraint_dict['label'] = set(labels)
        elif not ptoken.alpha.isupper():
            constraint_dict['terminal'] = {ptoken.alpha}

        for key, value_set in ptoken.constraints_list:
            value_set = set(value_set)
            if key in constraint_dict:
                constraint_dict[key].update(value_set)
            else:
               constraint_dict[key] = value_set
        return cls.PatternToken(ptoken.alpha + ptoken.num, constraint_dict)

def add_properties(prop_tree):
    for node in prop_tree.descendant_or_self():
        node.properties['terminal'] = node.terminals

class ConceptualGraph:

    Node = namedtuple('Node', ['id_', 'label', 'type'])
    Edge = namedtuple('Edge', ['left', 'right'])

    type_map = {
        'relation' : 'shape=box',
        'statement' : 'shape=polygon',
        None : 'shape=ellipse'
    }

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_edge(self, left, right):
        if left not in self.nodes:
            self.nodes.append(left)
        if right not in self.nodes:
            self.nodes.append(right)
        self.edges.append(ConceptualGraph.Edge(left, right))

    def get_by_id(self, id_):
        for node in self.nodes:
            if node.id_ == id_:
                return node

    def to_dot(self):
        dot_code = ['digraph{', 'rankdir=LR;']

        for node in self.nodes:
            label = 'label=' + '"' + node.label + '"'
            type_ = ConceptualGraph.type_map[node.type]
            content = ', '.join([label, type_])
            line = ['N' + str(node.id_), '[', content, ']']
            dot_code.append(' '.join(line))

        for edge in self.edges:
            right = 'N' + str(edge.right.id_)
            left  = 'N' + str(edge.left.id_)
            line  = [left, '->', right]
            dot_code.append(' '.join(line))

        dot_code.append('}')

        return '\n'.join(dot_code)


class GraphBuilder:
    
    def __init__(self, pattern_matcher):
        self.pattern_matcher = pattern_matcher

    def build(self, sents):

        # tokenize sentences
        if isinstance(sents, str):
            sents = sents.lower() # convert to lower case !!!
            sents = [
                nltk.word_tokenize(s)
                for s in nltk.sent_tokenize(sents)
            ]

        logging.info('Construnct parsetree for all sentences!')
        parse_trees = stanford_parser.parse_sents(sents)

        for pt, sent in zip(parse_trees, sents):

            pt = list(pt)[0][0] # convert to list get tree and remove root node
            
            #import threading; threading.Thread(None, pt.draw).start()
            pt.draw()

            logging.debug('ParseTree:' + pformat(pt))

            logging.info('Construct property trees from parsetrees!')
            prop_tree = PropertyTree.from_parsetree(pt)
            add_properties(prop_tree)
            logging.debug(str(prop_tree))

            tmp_list = [
                (match.relations, match.transformation)
                for match in self.pattern_matcher.match_rules(prop_tree)]
            
            if len(tmp_list) == 0:
                logging.info('No match for: "' + ' '.join(sent) + '"')
                continue

            relations, transformations = zip(*tmp_list)

            trans_dict = dict(transformations)
            trans_dict = {
                key : trans_dict[value] if value in trans_dict else value
                for key, value in trans_dict.items()}

            transformed_relations = []
            for left, right in chain(*relations):
                if left in trans_dict:
                    left = trans_dict[left]
                if right in trans_dict:
                    right = trans_dict[right]
                transformed_relations.append((left, right))

            graph = ConceptualGraph()

            id_counter = count()
            for left, right in transformed_relations:

                left_id = next(id_counter) if isinstance(left, str) else id(left)
                right_id = next(id_counter) if isinstance(right, str) else id(right)

                left_node = graph.get_by_id(left_id)
                right_node = graph.get_by_id(right_id)

                if left_node is None:
                    left_node = ConceptualGraph.Node(
                        id_=left_id,
                        label=left if isinstance(left, str) else left['terminal'],
                        type=contsituen2type(None if isinstance(left, str) else left['label']))

                if right_node is None:
                    right_node = ConceptualGraph.Node(
                        id_=right_id,
                        label=right if isinstance(right, str) else right['terminal'],
                        type=contsituen2type(None if isinstance(right, str) else right['label']))
                
                graph.add_edge(left_node, right_node)

            yield graph


class PatternMatcher:

    Match = namedtuple('Match', ['prop_tree', 'rule', 'head_match',
                                 'pattern_match', 'relations', 'transformation'])

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
            
            #pt.draw()
            logging.debug('ParseTree:' + pformat(pt))

            logging.info('Construct property trees from parsetrees!')
            prop_tree = PropertyTree.from_parsetree(pt)
            add_properties(prop_tree)
            logging.debug(str(prop_tree))

            yield from self.match_rules(prop_tree)


    def match_rules(self, prop_tree):

        if self.head_only_ones:
            matched_nodes = [] # list of roots that have already been matched

        for rule in self.rules:

            head, pattern, _, _ = rule

            for head_node in prop_tree.descendant_or_self():

                satisfies_constaints = head_node.has_properties(**head.constraints)

                logging.debug(
                    'HEAD_TRY:\n Constraints: %s\n Properties: %s\n> %s!'
                    %(str(head.constraints), str(head_node.properties),
                        'YES!' if satisfies_constaints else 'NO!'))

                if not satisfies_constaints:
                    continue
                if self.head_only_ones and head_node in matched_nodes:
                    continue
                
                if self.whole:
                    start_nodes = head_node.no_preceding()
                else:
                    start_nodes = head_node.descendant_or_self()
                
                for match in self._search(start_nodes, pattern, head_node):

                    # TODO -- check for double varnames ?
                    match_dict = dict(match)
                    match_dict[head.varname] = head_node

                    relations = [
                        (match_dict[left], match_dict[right])
                        for left, right in rule.relations
                        ]

                    transformation = (
                        head_node,
                        match_dict[rule.transformation] if rule.transformation in match_dict else rule.transformation
                        )
                    head_match = (head.varname, head_node)

                    yield PatternMatcher.Match(
                        prop_tree, rule, head_match,
                        match, relations, transformation)

                    if self.head_only_ones:
                        matched_nodes.append(head_node)
                        break


    def _search(self, nodes, pattern, head_node, match=None, index=0):

        if match is None:
            match = [None]*len(pattern)

        if len(pattern) == index:
            if self.whole:
                nodes = list(nodes)
                
            if self.whole and len(nodes):
                #print(nodes, index)
                logging.debug('Match, but not whole.')
            else:
                logging.debug('Pattern matched!!!')
                yield tuple(match)

        else:
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

                imidiate_following = node.imidiate_following(root=head_node)

                yield from self._search(imidiate_following, pattern, head_node, match, index+1)


    @classmethod
    def from_str(cls, rules_str):
        parser = RuleParser()
        rules = parser.parse_rules(rules_str)
        return cls(rules)

    class PatternMatchingError(Exception):
        pass



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
            if node!=root and node.parent and node.parent.children:
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
    

def main():
    import sys; args=sys.argv[1:]

    if not args:
        raise Warning('Need sentences!')
        sys.exit(0)

    logging.basicConfig(level=logging.INFO)

    sents = args[0]

    with open('rules') as f:
        rules = f.read()

    matcher = PatternMatcher.from_str(rules)
    builder = GraphBuilder(matcher)

    for graph in builder.build(sents):
        dot_code = graph.to_dot()
        print(dot_code)

    """print()
    print()
    print('Check matches first!!!')
    for match in matcher.match(sent):
        prop_tree, rule, head_match, pattern_match, _r, _t  = match

        hm_varname,  hm_node  = head_match
        pm_varnames, pm_nodes = zip(*pattern_match)

        hm_label = hm_node['label']
        pm_labels = [n['label'] for n in pm_nodes]

        hm_term = hm_node['terminal']
        pm_terms = [n['terminal'] for n in pm_nodes]

        print()
        print(sent)
        print(' ', hm_varname, '\t| ', '\t'.join(pm_varnames))
        print(' ', hm_label, '\t| ', '\t'.join(pm_labels))
        print()
        print(hm_label, '▶', hm_term)
        for L,T in zip(pm_labels, pm_terms):
            print(L, '▶', T)

        input()"""


if __name__ == '__main__':
    main()