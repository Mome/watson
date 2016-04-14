from itertools import chain, islice
import nltk
from collections import namedtuple

Rule = namedtuple('Rule',['head','pattern'])
PatternToken = namedtuple('PatternToken',['label','id'])

def parse_rule(rule_str):
    head, pattern_str = [r.strip() for r in rule_str.split(':')]

    pattern = []
    for pattern_token in pattern_str.split():
        if not pattern_token:
            continue
        if '_' in pattern_token:
            label, id_ = pattern_token.split('_')
        else:
            label = pattern_token
            id_ = None
        pattern.append(PatternToken(label, id_))

    return Rule(head, pattern)

def match_rule(rule, tree):
    ...


"""

class PropertyTree(IteratorTree):

    def __init__(self, parent=None, children=None, **keyargs):
        super(self).__init__(self, parent, children)
        self.__dict__.update(keyargs)

    @classmethod
    def from_nltktree(cls, nltktree, parent=None):
        ptree = PropertyTree(label=nltktree.label)
        ptree.children = [from_nltktree(subtree, ptree) for subtree in nltktree]
        return ptree


class IteratorTree:
    def __init__(self, parent=None, children=None):
        self.children = [] if (children is None) else children
        self.parent = parent     

    @property
    def ancestors(self):
        parent = self.parent
        while parent:
            yield parent
            parent = parent.parent

    @property
    def ancestors_or_self(self):
        return chain([self], self.ancestors)

    @property
    def descendant(self):
        return chain.from_iterable(
            child.descendant for child in self.children) 

    @property
    def descendant_or_self(self):
        return chain([self], self.descendant)

    @property
    def siblings(self):
        for node in self.parent.children:
            if node not is self:
                yield node

    @property
    def siblings_or_self(self):
        return iter(self.parent.children)

    @property
    def following(self):
        for ancestor in self.ancestors_or_self:
            for fosib in ancestor.following_sibling:
                for follower in fosib.descendant_or_self:
                    yield follower

    @property
    def following_sibling(self):
        siblings = self.parent.children
        i = siblings.index(self)
        return islice(siblings, i+1, None)

    @property
    def preceding_sibling(self):
        siblings = self.parent.children
        i = siblings.index(self)
        return islice(siblings, i-1)

    @property
    def imidiate_following(self):
        for desos in self.descendant_or_self:
            folsib = list(following_sibling)
            if len(folsib) == 0:
                continue
            next_sibling = folsib[0]
            for node in next_sibling.firstborn_descendant_or_self:
                yield node

    @property
    def firstborn_descendant_or_self(self):
        yield self
        node = self
        while node.children:
            node = children[0]
            yield node


def TreeList(list):
    def __getattr__(self, name):
        return TreeList(getattr(tree, name) for tree in self)"""





