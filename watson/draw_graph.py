import os
import subprocess

from nltk.tree import Tree

import configurations as conf


def draw_parsetree(tree, engine='nltk', id_=0):
    """ Takes a sentence and draws the parsetree in an extra window. """

    # if tree in string representation convert to nltk.Tree object
    if isinstance(tree,(str,unicode)):
        tree = Tree.fromstring(tree)

    if engine == 'nltk' :
        tree.draw()

    elif engine == 'graphviz' :
        png_path = 'temp_tree_' + str(id_) + '.png'
        dot_code = nltk_tree_to_dot(tree)
        dot_to_image(dot_code, 'temp_tree_' + str(id_))
        subprocess.call([conf.image_viewer, png_path])

def nltk_tree_to_dot(tree) :
    """ Transforms a nltk.Tree in a digraph dotcode"""
    
    dot_code = 'digraph graphname {\n'
    dot_code += str(0) + ' [label="' + tree.label() + '"];\n'

    def get_subtrees(tree,node_number=0,terminals = '{ rank=same; '):
        dot_code = ""

        father_node_number = node_number

        for child in tree:

            node_number+=1

            if type(child) in [str,unicode] :
                dot_code += str(node_number) + ' [label="' + child + '" shape=box];\n'
                dot_code += str(father_node_number) + ' -> ' + str(node_number) + '\n'
                terminals += str(node_number) + '; '
            else :
                dot_code += str(node_number) + ' [label="' + child.label() + '"];\n'
                dot_code += str(father_node_number) + ' -> ' + str(node_number) + '\n'
                new_code, node_number, terminals = get_subtrees(child,node_number,terminals)
                dot_code += new_code

        return dot_code, node_number, terminals

    new_code, _, terminals = get_subtrees(tree)
    dot_code += terminals + '}\n'
    dot_code += new_code + '}'

    return dot_code


def dot_to_image(dot_code, name) :
    """ Creates an png image from dot-code"""
    tmp_file = 'temp.dot'
    f = open(tmp_file, 'w')
    f.write(dot_code)
    f.close()
    os.popen('dot temp.dot -Tpng -o' + name + '.png')
    os.remove('temp.dot')



### Rest is unimportant ...
# functions to draw graphs or triple stores

def build_triple_code(tripel_list):
    dot_code = ""
    for tripel in tripel_list:
        dot_code += '"' + tripel[0] + '" -> "' + tripel[2] + '" [label="'+ tripel[1] + '"]\n'
    return dot_code


def list_of_tripels_to_dot(tripel_list):
    dot_code = 'digraph graphname {\n'
    dot_code += build_triple_code(tripel_list)
    return dot_code + '}'


def list_of_tripels_to_dot_fancy(tripel_list):
    dot_code = 'digraph graphname {\n'
    dot_code += 'rankdir=LR\n'
    dot_code += 'node [shape=box]\n'

    node_shape_list = []
    for i,tripel in enumerate(tripel_list) :
        if tripel[1] == 'to_verb' :
            node_shape_list.append(tripel[2] + ' [shape=diamond]')
            tripel_list[i] = (tripel[0],'',tripel[2])
        elif tripel[1] == 'from_verb' :
            node_shape_list.append(tripel[0] + ' [shape=diamond]')
            tripel_list[i] = (tripel[0],'',tripel[2])
        elif tripel[1] == 'property_of' :
            node_shape_list.append(tripel[0] + ' [shape=egg]')
    
    for s in set(node_shape_list) :
        dot_code += s+'\n'

    dot_code += build_triple_code(tripel_list)

    return dot_code + '}'