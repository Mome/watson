# The idea is to have a language to match certain patterns in parse trees
# and translate them to some kind of a semantic structure

from copy import copy

from nltk.tree import Tree, ParentedTree

from configurations import tree_patterns_path, pattern_semantic_separator
import find_answers 
import recources as res


def load_pattern_list():

    with open(tree_patterns_path) as pattern_file:
        pattern_list = pattern_file.readlines()

    # cut out comments
    pattern_list = [line[:line.index('#')] if '#' in line else line for line in pattern_list]

    # remove empty lines
    pattern_list = [line.strip() for line in pattern_list if line.strip()!=''] 

    # splits line into pattern and semantics
    pattern_list = [line.split(pattern_semantic_separator) for line in pattern_list]
    
    # splits patterns and corresponding semantics into subparts
    pattern_list = [[pair[0].strip().split(),pair[1].strip().split()] for pair in pattern_list]

    patterns, semantic_tranlations = zip(*pattern_list)

    return patterns, semantic_tranlations


class TreePatternMatcher :

    def __init__(self):
        pattern_list, semantic_tranlations = load_pattern_list()
        self.pattern_list = pattern_list
        self.semantic_tranlations = semantic_tranlations

        self.function_dict = {
            'dbpedia' : res.dbpedia_wrapper,
            'wordnet' : res.get_wordnet_definition,
            'wiki' : res.get_first_wikipedia_sentences,
            'print': find_answers._print,
            'definition' : res.get_definition,
            'search' : find_answers.document_search_wrapper,
        }

    def match_all(self, tree, whole_sentence):
        match_tree = TreePatternMatcher._transform_match_tree(tree)
        matches = []
        for pattern in self.pattern_list :
            #print pattern
            #print match_tree.work_tree.pprint().replace(' ','').replace('\n',' ')
            matches += [self.match_pattern(pattern, match_tree, whole_sentence)]
        return matches        

    # matching has the find first 
    def match_pattern(self, pattern, match_tree, whole_sentence=False):
        
        pattern = self._transform_pattern(pattern)
        pattern = copy(pattern)    
     
        # cut part after underscore
        for i,p in enumerate(pattern) :
            if '$' in p :
                pattern[i] = p.split('$')[0]
        
        #isinstance(match_tree, (str,unicode,Tree))

        if whole_sentence :
            starters = match_tree.follower_dict[None]
        else :
            starters = match_tree.get_all_nodes()

        current_match = [-1]*len(pattern)

        def _match(nodes, index):

            matches = []

            for node in nodes :
                # here is the actual comparison :
                if pattern[index] != node.label() :
                    continue

                current_match[index] = node

                followers = match_tree.follower_dict[node]

                if index+1==len(pattern) :
                    if whole_sentence and followers :
                        continue
                    matches += [copy(current_match)]

                elif followers:
                    matches += _match(followers, index+1)

            return matches

        matches = _match(starters, 0)

        return matches


    def semantics_all(self, all_matches,silent=True):

        answers = []

        for i,matches in enumerate(all_matches):
            s = self.semantic_tranlations[i]
            if s[0] in ['none','None'] :
                if not silent: print 'Empty semantic!'
                continue
            p = self.pattern_list[i]
            for m in matches :
                answers += self.match_to_semantics(p,m,s)
        return answers


    def match_to_semantics(self, pattern, match, semantic):
        
        output = []

        #match_labels = [m.label() for m in match]
        match_terminals = [" ".join(MatchTree.get_terminals(m)) for m in match]
        sem_func, sem_args = zip(*[s.split(':') for s in semantic])
        sem_args = [a.split(',') for a in sem_args]
        
        #print 'sem_func', sem_func
        #print 'sem_args', sem_args
        #print 'match_labels', match_labels
        #print 'match_terminals', match_terminals
        #print 'pattern', pattern        
 
        for func,args in zip(sem_func,sem_args) :
            arg_terminals = []
            for a in args :
                if a in pattern :
                    arg = match_terminals[pattern.index(a)]
                else :
                    arg = a
                arg_terminals.append(arg)
            
            #print 'arg_terminals', arg_terminals
            print 'looking for answer with ' + func + '...'
            output += [self.function_dict[func](*arg_terminals)]

        return output


    def _transform_pattern(self, pattern):

        if type(pattern) == int :
            pattern = self.pattern_list[pattern]
        elif type(pattern) in [str,unicode]:
            pattern = pattern.strip().split()
        else :
            pattern = list(pattern)

        return pattern


    @classmethod
    def _transform_match_tree(cls, tree):
        """ converts a Tree (string or nltk string) into a MatchTree """
        
        if isinstance(tree, (str,unicode,Tree)) :
            match_tree = MatchTree(tree)
        elif not isinstance(tree, MatchTree) :
            raise Exception('Type: ' + str(type(tree)) + \
                ' not convertable to MatchTree !')

        return match_tree


class MatchTree :

    def __init__(self, tree_or_str):

        if type(tree_or_str) == Tree:
            self.original_tree = tree_or_str
        else :
            self.original_tree = Tree.fromstring(tree_or_str)

        self.work_tree = self._construct_work_tree()
        self.label_dict = self._construct_label_dict()
        self.follower_dict = self._construct_follower_dict()

    @classmethod
    def get_terminals(cls,node):

        if len(node) == 0 :
            return [node.label()]

        terminals = []
        for subnode in node.subtrees() :
            if len(subnode) == 0 :
                terminals.append(subnode.label())

        return terminals

    def get_all_nodes(self):
        return list(self.work_tree.subtrees()) + [self.work_tree]

    def _construct_work_tree(self) :
        # adds numbers to node 543
        work_tree = ParentedTree.convert(self.original_tree)

        # wrap leaves
        def wrap_leaves(node):
            for i,child in enumerate(node) :
                if isinstance(child, Tree):
                    wrap_leaves(child)
                else :
                    node[i] = ParentedTree(child,[])

        wrap_leaves(work_tree)

        # freeze worktree to use as key in dict
        return work_tree.freeze()

    def _construct_label_dict(self):
        label_dict = {}
        for node in self.work_tree.subtrees() :
            if node.label() in label_dict :
                label_dict[node.label()].append(node)
            else :
                label_dict[node.label()] = [node]
        return label_dict

    def _construct_follower_dict(self):
        follower_dict = {}
        follower_dict[None] = self._get_followers(None)
        follower_dict[self.work_tree] = []
        for node in self.work_tree.subtrees() :
            #print node.label()
            follower_dict[node] = self._get_followers(node)
        return follower_dict

    def _get_followers(self, node):

        if node == None :
            tmp_node = self.work_tree
        else :
            # find next right sibling,uncle,great uncle ...
            tmp_node = node
            while tmp_node.right_sibling() == None :
                tmp_node = tmp_node.parent()
                if tmp_node == None :
                    return []
            tmp_node = tmp_node.right_sibling()

        # get line of first children
        followers = []
        while list(tmp_node) !=  []:
            followers.append(tmp_node)
            tmp_node = tmp_node[0]
        followers.append(tmp_node)

        return followers

    
