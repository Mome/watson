from itertools import chain, islice, tee
import nltk
from collections import namedtuple
import os
from nltk.parse import stanford
import logging
from copy import copy
from pprint import pformat, pprint
#logging.basicConfig(level=logging.INFO)


stanford_path = os.path.expanduser('~/.local/stanford-parser-full-2015-12-09')
os.environ['STANFORD_MODELS'] = stanford_path
os.environ['STANFORD_PARSER'] = stanford_path
stanford_parser = stanford.StanfordParser() 


Rule = namedtuple('Rule',['head','pattern'])
PatternToken = namedtuple('PatternToken',['varname','constraints'])
Match = namedtuple('Match', ['varnames', 'nodes'])

constituent_list = ['NP', 'VP', 'DT','NNS','.']

def parse_rule(rule_str):
    head, pattern_str = [r.strip() for r in rule_str.split('::')]

    pattern = []
    for pattern_token in pattern_str.split():

        if not pattern_token:
            continue

        if ':' in pattern_token:
            varname, constraints = pattern_token.split(':')
            constraints = dict(const.split('=') for const in constraints.split(','))
        else:
            varname = pattern_token
            constraints = {}

        if '_' in varname:
            label, _ = varname.split('_')
        else:
            label = varname

        if label in constituent_list:
            constraints['label'] = label
        else:
            constraints['terminal'] = label

        pattern.append(PatternToken(varname, constraints))

    return Rule(head, pattern)


def add_properties(prop_tree):
    for node in prop_tree.descendant_or_self:
        node.properties['terminal'] = node.terminals

class PatternMatcher:
    def __init__(self, rules):
        self.rules = rules


    def match(self, sents):

        if isinstance(sents, str):
            sents = [
                nltk.word_tokenize(s)
                for s in nltk.sent_tokenize(sents)
            ]

        print(sents)

        logging.info('Construnct parsetree for all sentences!')
        parse_trees = stanford_parser.parse_sents(sents)
        matches_for_sentences = []
        for pt in parse_trees:
            pt = list(pt)[0][0] # convert to list get tree and remove root node
            pt.draw()
            logging.debug('ParseTree:' + pformat(pt))

            match = self.match_rules(pt)
            matches_for_sentences.append(match)

        return matches_for_sentences


    def match_rules(self, parse_tree):

        logging.info('Construct property trees from parsetrees!')
        prop_tree = PropertyTree.from_parsetree(parse_tree)
        add_properties(prop_tree)
        logging.debug(str(prop_tree))

        matched_nodes = [] # list of constrinutes that have already been matched
        rule_matches = [list() for _ in range(len(self.rules))] # stores a match for each rule.

        for i, (head, pattern) in enumerate(self.rules):

            # find nodes with head-label (roots of subtrees)
            for node in prop_tree.descendant_or_self:
                if node.properties['label'] != head:
                    continue
                if node in matched_nodes:
                    continue

                matches = PatternMatcher.match_pattern(pattern, node)

                if len(matches) > 1:
                    logging.warning('multiple matches for rule ' + str(i))

                if len(matches) == 0:
                    match = None
                else:
                    match = matches[0]

                rule_matches[i].append(match)

        return rule_matches


    @staticmethod
    def match_pattern(pattern, root_node, whole=True):

        # --------------------------------------- #
        def search(node, index=0):

            varname, constraints = pattern[index]

            imidiate_following = list(node.imidiate_following)
            #print('\nnode:', node, 'imidiate_following:', len(imidiate_following))

            logging.debug(
                    'TRY:%i\n Constraints: %s\n Properties: %s'
                    %(index, str(constraints), str(node.properties)))

            if not node.has_properties(**constraints):
                logging.debug('NO\n')
                return
            logging.debug('YES\n')

            # assign node to variable
            match[index] = (varname, node)

            if len(pattern)-1 == index:

                if whole and len(imidiate_following):
                    logging.debug('Match, but not whole.')
                    return

                logging.debug('Pattern match!!!')
                match_list.append(copy(match))
                return

            for next_node in imidiate_following:
                search(next_node, index+1)
        # --------------------------------------- #

        match_list = [] # stores matches
        match = [None]*len(pattern) # this works only, because matches have always the same length

        if whole:
            start_nodes = root_node.no_preceding
        else:
            start_nodes = root_node.descendant_or_self

        start_nodes = list(start_nodes)
        logging.debug('start_nodes' + str([n.properties['label'] for n in start_nodes]) + '\n')

        for node in start_nodes:
            search(node)

        return match_list


    @classmethod
    def from_str(cls, lines):
        if isinstance(lines, str):
            lines = lines.splitlines()
        lines = [line.strip() for line in lines if line.strip()]
        rules = [parse_rule(line) for line in lines]
        for r in rules: logging.debug('\n' + pformat(dict(r._asdict())))

        return cls(rules)



class IteratorTree:
    def __init__(self, parent=None, children=None):
        self.children = []
        if children: self.add_children(*children)
        self.parent = parent

    def add_children(self, *children):
        for child in children: child.parent=self
        self.children += children

    @property
    def ancestor(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    @property
    def ancestor_or_self(self):
        return chain([self], self.ancestor)

    @property
    def descendant(self):
        #return chain.from_iterable(
        #    child.descendant_or_self for child in self.children)
        return islice(self.descendant_or_self, 1, None)

    @property
    def descendant_or_self(self):
        yield self
        for child in self.children:
            for des in child.descendant_or_self:
                yield des

    @property
    def sibling(self):
        for node in self.parent.children:
            if not(node is self):
                yield node

    @property
    def sibling_or_self(self):
        return iter(self.parent.children)

    @property
    def following(self):
        for ancestor in self.ancestor_or_self:
            for fosib in ancestor.following_sibling:
                for follower in fosib.descendant_or_self:
                    yield follower

    @property
    def following_sibling(self):
        if self.parent:
            siblings = self.parent.children
            i = siblings.index(self)
            return islice(siblings, i+1, None)
        else:
            return iter(())

    @property
    def preceding(self):
        for ancestor in self.ancestor_or_self:
            for fosib in ancestor.preceding_sibling:
                for follower in fosib.descendant_or_self:
                    yield follower

    @property
    def preceding_sibling(self):
        if self.parent:
            siblings = self.parent.children
            i = siblings.index(self)
            #print('type --- ... ---', type(siblings), type(i), i)
            return islice(siblings, i)
        else:
            return iter(())

    @property
    def imidiate_following(self):

        def next_sibling(node):
            if node.parent and node.parent.children:
                i = node.parent.children.index(node)
                if len(node.parent.children) > i+1:
                    return node.parent.children[i+1]

        # find next sibling of ancestor or self
        for node in self.ancestor_or_self:
            next = next_sibling(node)
            if next:
                out = next.no_preceding # node and all firstborn
                break
        else:
            out = iter(())
        return out
        

    @property
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



class PropertyTree(IteratorTree):

    def __init__(self, parent=None, children=None, **keyargs):
        super(PropertyTree, self).__init__(parent, children)
        self.properties = keyargs

        # add IteratorTree as properties
        for prop in IteratorTree.__dict__:



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

        out = True
        for key, value in props.items():
            if not (key in self.properties):
                break
            if callable(value):
                value = value()
            if callable(self.properties[key]):
                self.properties[key] = self.properties[key]()
            if self.properties[key] != value:
                break
        else:
            out = False

        return out


    def __repr__(self):
        return self.__str__()
        

    def __str__(self):
        name = self.properties.get('label', self.__class__.__name__)
        if len(self.children)==0:
            return name + ' "' + self.terminals + '"'
        inner = ' '.join(str(c) for c in self.children)        
        return ''.join([name, '[ ', inner, ']'])


def TreeList(list):

    def constrain(self, properties):
        return TreeList( tree for tree in self
            if all( item in tree.properties.items() for item in properties.items()))

    def __getattr__(self, name):
        return TreeList(getattr(tree, name) for tree in self)

    def __call__(self, **keyargs):
        return self.constrain(keyargs)



if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)

    rules = """
    NP :: DT NN
    """
    # NP :: DT NN
    # 
    # S :: DT NN is NP
    # S :: DT NN VP

    sent = "The snake is a python."

    matcher = PatternMatcher.from_str(rules)
    matches = matcher.match(sent)

    print(matches)

    for i,match in enumerate(matches):
        print('\n\nMatches for Sent %i:'%i)
        for j,m in enumerate(match):
            print(j, m)
