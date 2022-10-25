"""
author: Natalia Mordvanyuk
email: natalia.mordvanyuk@udg.edu
created 15/08/2019
updated 18/03/2020

This file form part of the implementation of the vertTIRP algorithm described in the article:

Natalia Mordvanyuk, Beatriz López, Albert Bifet,
vertTIRP: Robust and efficient vertical frequent time interval-related pattern mining,
Expert Systems with Applications,
Volume 168,
2021,
114276,
ISSN 0957-4174,
https://doi.org/10.1016/j.eswa.2020.114276.
(https://www.sciencedirect.com/science/article/pii/S0957417420309842)
Abstract: Time-interval-related pattern (TIRP) mining algorithms find patterns such as “A starts B” or “A overlaps B”. The discovery of TIRPs is computationally highly demanding. In this work, we introduce a new efficient algorithm for mining TIRPs, called vertTIRP which combines an efficient representation of these patterns, using their temporal transitivity properties to manage them, with a pairing strategy that sorts the temporal relations to be tested, in order to speed up the mining process. Moreover, this work presents a robust definition of the temporal relations that eliminates the ambiguities with other relations when taking into account the uncertainty in the start and end time of the events (epsilon-based approach), and includes two constraints that enable the user to better express the types of TIRPs to be learnt. An experimental evaluation of the method was performed with both synthetic and real datasets, and the results show that vertTIRP requires significantly less computation time than other state-of-the-art algorithms, and is an effective approach.
Keywords: Time Interval Related Patterns; Temporal data mining; Sequential pattern mining; Temporal relations
"""

import queue
import numpy as np

class VertTirpNode:
    """
    VertTirpNode is created to represent a tree of patterns that have been found with the VertTirp
    algorithm.

    """

    #  By default Python uses a dict to store an object’s instance attributes.
    #  The dict wastes a lot of RAM. We use __slots__ to tell Python not to use a dict,
    #  and only allocate space for a fixed set of attributes
    __slots__ = ['patt', 'pat_len', 'parent', 'child_nodes', 'sidlist']

    def __init__(self, patt="", pat_len=0, parent=None, sidlist=None):
        self.patt = patt  # a sequence string
        self.pat_len = pat_len  # size of a tirp
        self.parent = parent  # a parent node
        self.child_nodes = []  # a list of children nodes
        self.sidlist = sidlist  # a sidlist

    def add_child(self, ch):
        """
        Append a child ch to the child_nodes vector
        :param ch: child node
        :return:
        """
        self.child_nodes.append(ch)

    def print_tree_dfs(self, min_len, o_file, events_per_sequence):
        """
        Prints in depth first search manner the patterns into the output file,
        or if it does not exists prints them on the screen
        :param min_len: minimum pattern length to be printed
        :param o_file: an output file to print patterns
        :return: prints in depth first search manner into the o_file,
        or if it does not exists prints them on the screen
        """
        if self.pat_len >= min_len:
            if o_file:
                o_file.write(str(self.patt)+'\n')
                for rel, tirp_stat in self.sidlist.definitive_discovered_tirp_dict.items():
                    o_file.write(str(rel) + " # ver: " + str(self.sidlist.get_ver_support(tirp_stat))
                                 + " # hor: " + str(self.sidlist.get_mean_hor_support(events_per_sequence,tirp_stat)) + " # duration: " + str(
                                tirp_stat.get_mean_of_means_duration()) + '\n')
            else:
                print(str(self.patt))
                for rel, tirp_stat in self.sidlist.definitive_discovered_tirp_dict.items():
                    print(str(rel) + " # ver: " + str(self.sidlist.get_ver_support(tirp_stat))
                          + " # hor: " + str(self.sidlist.get_mean_hor_support(events_per_sequence,tirp_stat))+ " # duration: " + str(
                                tirp_stat.get_mean_of_means_duration()))

        for n in self.child_nodes:
            n.print_tree_dfs(min_len, o_file,events_per_sequence)


    def analyze_patterns_rec(self,rels_pos,global_arr):
        """
        A function useful to analyze 2-lenght patterns to discover the best pairing strategy
        :param list_of_ti_seqs: a list of time intervals for each sequence
        :param list_of_seqs: a list of sequence names
        :param timestamp_mode: if True the date is in timestamp format (long number), otherwise in the datetime format
        :return: returns frequent relations between patterns of length 2 sorted from frequent to less frequent
        """

        if self.pat_len >= 2:
            local_arr = [0] * 8
            for rel, stat in self.sidlist.definitive_discovered_tirp_dict.items():
                local_arr[rels_pos[rel]] += stat.sum_ver_supp
            global_arr.append(local_arr)

        for n in self.child_nodes:
            n.analyze_patterns_rec(rels_pos,global_arr)

    def analyze_patterns(self,return_dict=True):
        """
        Function that returns the best pairing strategy
        :param return_dict: if True returns a dictionary sorted by relation frequency, otherwise returns
        a string of sorted relations.
        """
        rels_pos = dict()
        rels_pos['b'] = 0
        rels_pos['m'] = 1
        rels_pos['c'] = 2
        rels_pos['f'] = 3
        rels_pos['o'] = 4
        rels_pos['s'] = 5
        rels_pos['e'] = 6
        rels_pos['l'] = 7
        global_arr = []

        self.analyze_patterns_rec(rels_pos, global_arr)
        if not global_arr:
            sum_v = [0]*8
        else:
            sum_v = np.sum(global_arr, axis=0)

        global_dict = dict()
        for rel, pos in rels_pos.items():
            global_dict[rel] = sum_v[pos]

        if return_dict:
            return {k: v for k, v in sorted(global_dict.items(), key=lambda item: item[1], reverse=True)}
        else:
            sorted_rels = [k for k, v in sorted(global_dict.items(), key=lambda item: item[1], reverse=True) if v != 0]
            return ''.join(str(e) for e in sorted_rels)

    @staticmethod
    def print_tree_bfs(root=None, min_len=1, o_file=None, events_per_sequence=None):
        """
        Prints in breadth first search manner (by levels) the patterns into the output file,
        or if it does not exists prints them on the screen
        :param min_len: minimum pattern length to be printed
        :param root: the root node of the tree
        :param o_file: output file to print the patterns
        :return: prints in depth first search manner into the o_file,
        or if it does not exists prints them on the screen
        """
        if not root:
            return

        q = queue.Queue()
        q.put(root)

        current_level_count = 1
        next_level_count = 0

        while not q.empty():
            node = q.get_nowait()

            # print node data
            if node.pat_len >= min_len:

                for rel, tirp_stat in node.sidlist.definitive_discovered_tirp_dict.items():
                    r = [rr for rr in rel]
                    if o_file:
                        o_file.write(str(node.patt) + str(r) + " # ver: " + str(node.sidlist.get_ver_support(tirp_stat))
                                     + " # hor: " + str(node.sidlist.get_mean_hor_support(events_per_sequence,tirp_stat)) + " # duration: " + str(
                            tirp_stat.get_mean_of_means_duration()) + '\n')
                    else:
                        print(str(node.patt) + str(r) + " # ver: " + str(node.sidlist.get_ver_support(tirp_stat)) + " # hor: " + str(
                            node.sidlist.get_mean_hor_support(events_per_sequence,tirp_stat)) + " # duration: " + str(
                            tirp_stat.get_mean_of_means_duration()))

            # queue the children
            for ch in node.child_nodes:
                q.put(ch)
                next_level_count += 1

            current_level_count -= 1

            if current_level_count == 0:
                current_level_count = next_level_count
                next_level_count = 0

