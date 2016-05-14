import unittest
from tree_pattern import *


class TestIteratroTree(unittest.TestCase):

    def setUp(self):
        nodes = [IteratorTree() for _ in range(23)]
        A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W = nodes
        
        A.add_children(B)
        B.add_children(C,D,E,F,G)
        E.add_children(H,I,J,K,L)
        H.add_children(M)
        L.add_children(N)
        J.add_children(O,P,Q,R,S)
        P.add_children(T,U)
        S.add_children(V,W)

        letters = 'ABCDEFGHIJKLMNOPQRSTUVW'
        self.__dict__.update(dict(zip(letters, nodes)))
        for l in letters: self.__dict__[l].label=l

    def test_ancestors(self):
        a = frozenset(self.J.ancestor)
        b = frozenset([self.E, self.B, self.A])
        self.assertEqual(a,b)

    def test_ancestors_or_self(self):
        a = frozenset(self.J.ancestor_or_self)
        b = frozenset([self.J, self.E, self.B, self.A])
        self.assertEqual(a,b)

    def test_decendant(self):
        a = frozenset(self.J.descendant)
        #print([x.label for x in a])
        b = frozenset([self.O,self.P,self.Q,self.R,
            self.S,self.T,self.U,self.V,self.W])
        self.assertEqual(a,b)

    def test_decendant_or_self(self):
        a = frozenset(self.J.descendant_or_self)
        b = frozenset([self.J,self.O,self.P,self.Q,self.R,
            self.S,self.T,self.U,self.V,self.W])
        self.assertEqual(a,b)

    def test_sibling(self):
        a = frozenset(self.J.sibling)
        b = frozenset([self.H,self.I,self.K,self.L])
        self.assertEqual(a,b)

    def test_sibling_or_self(self):
        a = frozenset(self.J.sibling_or_self)
        b = frozenset([self.H,self.I,self.J,self.K,self.L])
        self.assertEqual(a,b)

    def test_following(self):
        a = frozenset(self.J.following)
        b = frozenset([self.F, self.G, self.K, self.L, self.N])
        self.assertEqual(a,b)

    def test_following_sibling(self):
        a = frozenset(self.J.following_sibling)
        b = frozenset([self.K, self.L])
        self.assertEqual(a,b)

    def test_preceding(self):
        a = frozenset(self.J.preceding)
        b = frozenset([self.C, self.D, self.H, self.I, self.M])
        self.assertEqual(a,b)

    def test_preceding_sibling(self):
        a = frozenset(self.J.preceding_sibling)
        b = frozenset([self.H, self.I])
        self.assertEqual(a,b)

    def test_imidiate_following(self):
        a = frozenset(self.O.imidiate_following)
        b = frozenset([self.P, self.T])
        self.assertEqual(a,b)

        a = frozenset(self.J.imidiate_following)
        b = frozenset([self.K])
        self.assertEqual(a,b)

        a = frozenset(self.W.imidiate_following)
        b = frozenset([self.K])
        self.assertEqual(a,b)

    def test_no_preceding(self):
        a = frozenset(self.E.no_preceding)
        b = frozenset([self.E, self.H, self.M])
        self.assertEqual(a,b)


class TestRuleParser(unittest.TestCase):

    def setUp(self):
        self.parser = RuleParser()

    def _test_simple(self):
        rules_str = """
        S :: NP VP
        """
        rule = self.parser.parse_rules(rules_str)[0]
        self.assertEqual(rule.head, RuleParser.PatternToken('S', {'label':{'S'}}))
        self.assertEqual(rule.pattern[0], RuleParser.PatternToken('NP', {'label':{'NP'}}))
        self.assertEqual(rule.pattern[1], RuleParser.PatternToken('VP', {'label':{'VP'}}))

    def test_complex(self):
        rules_str = """
        S[type=animal] :: NP[a={c,x}, b=0] VP
        """
        rule = self.parser.parse_rules(rules_str)[0]
        self.assertEqual(rule.head, RuleParser.PatternToken('S', {'label':{'S'},'type':{'animal'}}))
        self.assertEqual(rule.pattern[0], RuleParser.PatternToken('NP', {'label':{'NP'},'a':{'c','x'},'b':{'0'}}))
        self.assertEqual(rule.pattern[1], RuleParser.PatternToken('VP', {'label':{'VP'}}))


class TestPatternMatcher(unittest.TestCase):
    ...


if __name__ == '__main__':

    unittest.main()
