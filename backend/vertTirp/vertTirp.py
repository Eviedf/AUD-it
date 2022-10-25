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

import vertTirp.vertTirp_sidlist as sl
from vertTirp.vertTirp_node import VertTirpNode
from vertTirp.tirp.allen_relationsEPS import ttu
from numpy import ceil
import vertTirp.tirp.allen_relationsEPS as aleps

MAXGAP = 3155695200
MAXDURATION = 3155695200
MIN_DURATION = 0

class VertTIRP:
    """
     The implementation of the VertTIRP algorithm
    """
    __slots__ = ['time_mode', 'out_file', 'min_sup_rel', 'min_confidence', 'min_gap', 'max_gap', 'min_duration',
                 'max_duration', 'max_length', 'min_length', 'eps', 'events_per_sequence',
                 'tirp_count', 'min_sup', 'f1', 'vertical_db', 'tree','allen']

    def __init__(self, time_mode=1, out_file=None, min_sup_rel=0.5, min_confidence=-1, min_gap=0, max_gap=MAXGAP,
                 min_duration=MIN_DURATION, max_duration=MAXDURATION,
                 max_length=-1, min_length=1, eps=500, dummy_calc=False, ps="mocfbesl", trans=True):

        self.out_file = out_file  # output file
        self.events_per_sequence = dict()   # necessary for relative horizontal support
        self.min_sup_rel = min_sup_rel  # relative minimum vertical support
        self.min_confidence = min_confidence
        # gaps in seconds
        self.min_gap = min_gap  # minimum gap in seconds that is the gap between before consecutive elements
        self.max_gap = max_gap  # maximum gap in seconds that is the gap between before consecutive elements
        self.min_duration = min_duration # each event interval should have a duration of at least min_duration seconds
        self.max_duration = max_duration # each tirp should have a duration of at most min_duration seconds
        self.max_length = max_length  # maximum pattern length
        self.min_length = min_length  # minimum pattern length
        self.eps = eps  # karma lego epsilon in nanoseconds

        self.tirp_count = 0
        self.min_sup = 0  # absolute support
        # save positions where each sequence begins and ends
        self.f1 = []  # holds frequent 1-size items
        self.vertical_db = dict()  # holds database represented vertically
        self.tree = VertTirpNode()  # we will save the patterns in a tree structure

        self.time_mode = time_mode  #  1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)

        assert min_gap >= 0 and max_gap >= 0
        if min_gap != 0 or max_gap != 0:
            assert (min_gap < max_gap)

        # establish pairing strategy
        if not dummy_calc:
            self.allen = aleps.AllenPairing(dummy_calc, trans, eps, ps)
        else:
            self.allen = aleps.AllenDummy(dummy_calc, trans, eps)

    def print_patterns(self, dfs=True):
        """
        Prints patterns into output file, or if it does not exists prints them on the screen
        :param dfs: whether to print in depth first search or breadth-first search manner
        :return: prints patterns into an output file, or on the screen
        """
        if self.out_file:
            with open(self.out_file, 'w') as o_file:
                if dfs:
                    self.tree.print_tree_dfs(self.min_length, o_file, self.events_per_sequence)
                else:
                    self.tree.print_tree_bfs(self.tree, self.min_length, o_file, self.events_per_sequence)
        else:
            if dfs:
                self.tree.print_tree_dfs(self.min_length, None,  self.events_per_sequence)
            else:
                self.tree.print_tree_bfs(self.tree, self.min_length, None,  self.events_per_sequence)

    def mine_patterns(self, list_of_ti_seqs, list_of_seqs, avoid_same_var_states=True):
        """
        A function to mine patterns.
        :param list_of_ti_seqs: a list of time intervals for each sequence
        :param list_of_seqs: a list of sequence names
        :param avoid_same_var_states: avoid mining states of the same variable, such as
        cgm.a  cgm.b cgm.c, so that at least one variable will be between them, e.g.
        cgm.a  CH.a cgm.b CH.a cgm.c
        :return: A tree (which store tirps) is constructed and the number of tirps is returned.
        """

        # Scans SDB to create V(SDB) to identify F1, the list of frequent items
        self.to_vertical(list_of_ti_seqs, list_of_seqs)

        procs = []

        # depth first tree traversal to mine patterns
        for i in range(len(self.f1)):
            # we will save patterns in the self.tree
            self.dfs_pruning(self.vertical_db[self.f1[i]], self.f1,
                                 VertTirpNode(patt=str(self.vertical_db[self.f1[i]].seq_str), pat_len=1, parent=self.tree,
                                              sidlist=self.vertical_db[self.f1[i]]), self.tree, avoid_same_var_states)

        return self.tirp_count

    def dfs_pruning(self, pat_sidlist, f_l, node, father, avoid_same_var_states=True):
        """
        Performs the recursive depth first tree traversal, and constructs the self.tree with tirps

        :param pat_sidlist: current sidlist
        :param f_l: lenght 1 frequent items
        :param node: the correspondent node to the pat_sidlist
        :return: constructs the self.tree branch corresponding to the pat_sidlist element
        """

        father.add_child(node)

        if pat_sidlist.seq_length >= self.min_length:
            self.tirp_count += len(pat_sidlist.definitive_discovered_tirp_dict)

        s_temp = dict()

        #  to control the maximum length
        if (self.max_length == -1) or ((self.max_length != -1) and ((pat_sidlist.seq_length + 1) <= self.max_length)):

            for s in f_l:
                if not self.same_variable(s, pat_sidlist.seq_str[-1], avoid_same_var_states):
                    s_bm = pat_sidlist.join(self.vertical_db[s], self.allen, self.eps, self.min_gap, self.max_gap, self.max_duration, self.min_sup, self.min_confidence)
                    if s_bm.definitive_ones_indices_dict:
                        s_temp[s] = s_bm

            s_syms = list(s_temp.keys())
            for j, j_pat in s_temp.items():
                s_node = VertTirpNode(patt=str(j_pat.seq_str), pat_len=j_pat.seq_length, parent=node, sidlist=j_pat)
                self.dfs_pruning(j_pat, s_syms, s_node, node, avoid_same_var_states)

    def same_variable(self, sym1, sym2, avoid_same_var_states=True):
        """
        :param sym1: symbol of the first time interval
        :param sym2: symbol of the second time interval
        :param avoid_same_var_states: whether exists the restriction of mining variables of the same state
        :return:
        """
        if not avoid_same_var_states:
            return False

        sym1_c = sym1.split("_")
        sym2_c = sym2.split("_")
        return sym1_c[0] == sym2_c[0]


    def to_vertical(self, list_of_ti_seqs, list_of_seqs):
        """
        Constructs the vertical database representation.
        For each frequent item there are an sidlist representation of that item, which is stored in the
        self.vertical_db

        :param list_of_ti_seqs: a list of time intervals of all sequences
        :param list_of_seqs: a list of sequence names
        :param time_mode:  1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :return:
        """
        eid = 0  # transaction or item-set id

        for [item_sets], name in zip(list_of_ti_seqs, list_of_seqs):
            self.events_per_sequence[name] = item_sets.size  # necessary for relative horizontal support (for descriptive purposes)
            for its in item_sets:

                #  duration constraints
                if (ttu(its.ti.end - its.ti.start, self.time_mode) >= self.min_duration) and (ttu(its.ti.end - its.ti.start, self.time_mode) <= self.max_duration):

                    if not (its.ti.sym in self.vertical_db):
                        self.vertical_db[its.ti.sym] = sl.VertTirpSidList(self.time_mode)
                        first_item = True  # sidlist for a new item
                    self.vertical_db[its.ti.sym].append_item(its.ti, name, eid)

                    eid += 1
            eid = 0

        # calculate the absolute support based on number of sequences
        n_sequences = len(list_of_seqs)
        self.min_sup = ceil(self.min_sup_rel * n_sequences)
        if self.min_sup == 0:
            self.min_sup = 1

        # save a set of frequent 1-sized items sorted lexicographically
        for it_name in list(self.vertical_db.keys()):
            if self.vertical_db[it_name].get_support() >= self.min_sup:
                self.vertical_db[it_name].set_n_sequences(n_sequences)
                self.f1.append(it_name)
            else:
                del self.vertical_db[it_name]

        self.f1 = sorted(self.f1)


