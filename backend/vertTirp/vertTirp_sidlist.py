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

import numpy as np
from vertTirp.tirp.tirp import TIRP
from vertTirp.tirp.tirp_statistics import TIRPstatistics

MAXGAP = 3155695200
MAXDURATION = 3155695200

__slots__ = ['time_mode', 'seq_str', 'seq_length', 'definitive_ones_indices_dict','definitive_discovered_tirp_dict', 'temp_discovered_tirp_dict', 'n_sequences']
class VertTirpSidList:

    def __init__(self, time_mode=False):

        # if True the date is in timestamp format (long number), otherwise in the datetime format
        self.time_mode = time_mode
        # a sequence of syms, e.g "ABC"
        self.seq_str = []
        # a sequence length
        self.seq_length = 0

        # where key is sequence id and value is a dict of eids and tirps
        self.definitive_ones_indices_dict = dict()
        # where key will be a relation string, e.g. "<<<"
        # and value will be the TIRP_statistics
        self.definitive_discovered_tirp_dict = dict()

        # first we save all in a temporal variable, but once the support>= min_support,
        # we save it a self.definitive_discovered_tirp_dict, and copy tirps to the
        # correspondent self.definitive_ones_indices_dict
        self.temp_discovered_tirp_dict = dict()
        self.n_sequences = 0

    def append_item(self, ti, sid, eid):
        """
        Method called during V(DB) creation, that adds a tirp to the sidlist
        corresponding event id.

        :param ti: a time interval to add to the sidlist
        :param sid: the sequence id
        :param eid: event id
        :param first_item: if it is set to True it is a new sidlist, otherwise it is an existent one.
        :return: Nothing. A tirp was added to the sidlist
        """
        new_tirp = TIRP([ti], ti.start, ti.end, r=[])

        if not self.definitive_discovered_tirp_dict:
            self.definitive_discovered_tirp_dict[" "] = TIRPstatistics(self.time_mode)
            self.seq_str = [ti.sym]
            self.seq_length = 1

        if not sid in self.definitive_ones_indices_dict:
            self.definitive_ones_indices_dict[sid] = dict()

        self.definitive_discovered_tirp_dict[" "].append_tirp(sid, eid, new_tirp)

        if not (eid in self.definitive_ones_indices_dict[sid]):
            self.definitive_ones_indices_dict[sid][eid] = [new_tirp]
        else:
            self.definitive_ones_indices_dict[sid][eid].append(new_tirp)

    def set_n_sequences(self,n_sequences):
        self.n_sequences = n_sequences

    def get_mean_hor_support(self, events_per_sequence, tirp_stat=None):
        """
        returns the horizontal support that is self.sum_hor_per_seq / self.sum_ver_supp
        :param events_per_sequence: a dictionary where key is a sequence id and value is number of items in sequence
        :return: returns the horizontal support that is self.sum_hor_per_seq / self.sum_ver_supp
        """
        return tirp_stat.get_mean_hor_support(events_per_sequence)

    def get_ver_support(self,  tirp_stat=None):
        """
        returns the vertical relative support
        :param n_sequences: total number of sequences
        :return: returns the vertical relative support
        """
        return tirp_stat.get_ver_support(self.n_sequences)

    def get_support(self):
        """
        returns the vertical relative support of 1-lenght pattern
        :param n_sequences: total number of sequences
        :return: returns the vertical relative support
        """
        return self.definitive_discovered_tirp_dict[" "].sum_ver_supp

    def join(self, f, ps, eps, min_gap=0, max_gap=MAXGAP, max_duration=MAXDURATION, min_ver_sup=0, min_confidence=0.9):
        """
        Performs a join between self and bm
        :param f: sidlist of length 1 to extend with
        :param ps: a pairing strategy
        :param eps: an epsilon to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_duration: maximum duration in seconds of a tirp
        :param min_ver_sup: minimum vertical support
        :return: a new sidlist, that is an extension of self with f
        """

        # a new sidlist new_sidlist to return
        new_sidlist = VertTirpSidList(self.time_mode)
        new_sidlist.seq_str = self.seq_str[:]
        new_sidlist.seq_str.append(f.seq_str[0])

        # a new sidlist will be extended with 1 item, so we increase its length 1 unit
        new_sidlist.seq_length = self.seq_length + 1

        new_sidlist.definitive_ones_indices_dict = dict()
        new_sidlist.definitive_discovered_tirp_dict = dict()
        new_sidlist.temp_discovered_tirp_dict = dict()
        new_sidlist.n_sequences = self.n_sequences
        new_sidlist.support = 0

        # whether to mine the last equal relation, to avoid mining A=A, or B=A when A=B have been mined previously
        mine_last_equal = self.seq_str[-1] < f.seq_str[0]

        for seq_id, dict_pos_tirps in self.definitive_ones_indices_dict.items():
            if seq_id in f.definitive_ones_indices_dict:
                f_eids = list(f.definitive_ones_indices_dict[seq_id].keys())
                last_f_first = f.definitive_ones_indices_dict[seq_id][f_eids[-1]][0].first
                first_f_first = f.definitive_ones_indices_dict[seq_id][f_eids[0]][0].first
                for self_first_eid, self_tirps in dict_pos_tirps.items():
                    # if there exists eids in f greater than my first eid
                    if self_first_eid < f_eids[-1]:

                        # first tirp
                        first_one_me = self_tirps[0]
                        # first tirp's start time
                        me_first = first_one_me.first

                        # determine from which point in time start to search
                        if min_gap > 0:
                            if self.time_mode != 2: # self.time_mode==1 or self.time_mode==3
                                me_first = first_one_me.first + min_gap
                            else:  # date time format self.time_mode==2
                                me_first = first_one_me.first + np.timedelta64(min_gap, 's')

                        # if last element of f, sidlist matchs the min gap restriction
                        if last_f_first >= me_first:

                            if max_gap != MAXGAP:                
                                if self.time_mode != 2: # self.time_mode==1 or self.time_mode==3
                                    me_second = me_first + max_gap
                                else: # date time format self.time_mode==2
                                    me_second = me_first + np.timedelta64(max_gap, 's')

                            # if last element of f sidlist matchs the max gap restriction
                            if (max_gap == MAXGAP) or \
                                    ((max_gap != MAXGAP) and
                                     first_f_first <= me_second):

                                f_dict_pos_tirps = f.definitive_ones_indices_dict[seq_id]
                                for f_pos, f_tirps in f_dict_pos_tirps.items():
                                    if (max_gap != MAXGAP) and f_tirps[0].first > me_second:
                                        break
                                    else:
                                        if f_pos > self_first_eid:
                                            ext_status = new_sidlist.update_tirp_attrs(seq_id, f_pos, f, mine_last_equal, ps, self.definitive_ones_indices_dict[seq_id][self_first_eid], eps, min_gap, max_gap, max_duration, min_ver_sup,self.definitive_discovered_tirp_dict,min_confidence)
                                            if ext_status == 2:
                                                # max_gap exceeded for all the tirps, break and
                                                # continue with another 1 of the self sequence
                                                # no sense prove out the next s event id, as max gap exceeded
                                                break
        del new_sidlist.temp_discovered_tirp_dict
        return new_sidlist

    def update_tirp_attrs(self, seq_id, f_eid, f_sidlist, mine_last_equal, ps, tirps_to_extend, eps, min_gap, max_gap, max_duration, min_ver_sup, father_discovered_tirp_dict,min_confidence):
        """
        Extends tirps_to_extend with f_sidlist of sequence seq_id, event f_eid
        :param seq_id: sequence id
        :param f_eid: event id in f
        :param f_sidlist: a frequent sidlist of length 1 to extend with
        :param mine_last_equal: whether to mine the last equal relation
        :param ps: a pairing strategy
        :param tirps_to_extend: a list of tirps to extend with
        :param eps: an epsilon to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_duration: maximum duration in seconds of a tirp
        :param min_ver_sup: minimum vertical support
        :param definitive_discovered_tirp_dict: father node discovered tirps. Necessary for confidence calculation
        :param min_confidence: minimum confidence
        :return: extends tirps_to_extend with f_sidlist of sequence seq_id, event f_eid and returns
         3 - if at least there is 1 tirp extension that does not exceed min gap nor max gap
         2 - if all tirps exceed max gap
         1 - otherwise, for example, min gap or max duration is not met
        """

        # time interval that will be added to each tirp_to_extend
        f_ti = f_sidlist.definitive_ones_indices_dict[seq_id][f_eid][0].ti

        all_max_gap_exceeded = True
        at_least_one_tirp = False

        for tirp_to_extend in tirps_to_extend:

            # the extension will return a new tirp and a status
            # status is: if ok:3, if max_gap: 2, otherwise: 1
            new_tirp, status = tirp_to_extend.extend_with(f_ti[0], eps, min_gap, max_gap, max_duration, self.time_mode, mine_last_equal, ps)

            if new_tirp is not None:
                at_least_one_tirp = True

                new_rel = new_tirp.get_rel_as_str()
                if new_rel not in self.temp_discovered_tirp_dict:  # if not exists
                    # create
                    self.temp_discovered_tirp_dict[new_rel] = TIRPstatistics(self.time_mode)

                # append it to a temporal discovered
                vert_supp = self.temp_discovered_tirp_dict[new_rel].append_tirp(seq_id, f_eid, new_tirp)

                # confidence calculation
                conf_constraint = True
                if min_confidence != -1:
                    if tirp_to_extend.get_rel_as_str() == '':
                        father_supp = father_discovered_tirp_dict[" "].sum_ver_supp
                    else:
                        father_supp = father_discovered_tirp_dict[tirp_to_extend.get_rel_as_str()].sum_ver_supp
                    conf_constraint = ((vert_supp / father_supp) >= min_confidence)

                if vert_supp >= min_ver_sup and conf_constraint:

                    if new_rel in self.definitive_discovered_tirp_dict:
                        # If the new_rel exists in the self.definitive_discovered_tirp_dict
                        self.definitive_discovered_tirp_dict[new_rel] = self.temp_discovered_tirp_dict[new_rel]

                        # update self.definitive_ones_indices_dict with a new_tirp
                        if seq_id not in self.definitive_ones_indices_dict:
                            self.definitive_ones_indices_dict[seq_id] = dict()

                        if f_eid not in self.definitive_ones_indices_dict[seq_id]:
                            self.definitive_ones_indices_dict[seq_id][f_eid] = [new_tirp]
                        else:
                            self.first_sorted_extend(seq_id, f_eid, [new_tirp])
                    else:
                        # If the new_rel does not exists in the self.definitive_discovered_tirp_dict
                        # what means that the new_rel just became frequent

                        self.definitive_discovered_tirp_dict[new_rel] = self.temp_discovered_tirp_dict[new_rel]

                        # copy all the frequent tirps at the correspondent event ids of
                        # self.definitive_ones_indices_dict
                        for sid, eid_tirps in self.definitive_discovered_tirp_dict[new_rel].sequence_events_tirps_dict.items():

                            for eid, tirps in eid_tirps.items():

                                if not sid in self.definitive_ones_indices_dict:
                                    self.support += 1
                                    self.definitive_ones_indices_dict[sid] = dict()

                                if not (eid in self.definitive_ones_indices_dict[sid]):
                                    self.definitive_ones_indices_dict[sid][eid] = tirps[:]
                                else:
                                    self.first_sorted_extend(sid, eid, tirps)
            else:
                if status != 2:
                    all_max_gap_exceeded = False

        if at_least_one_tirp:
            return 3
        elif all_max_gap_exceeded:
            return 2
        else:
            return 1

    def first_sorted_extend(self, sid, eid, new_tirps):
        """
        Adds new_tirps to the self.definitive_ones_indices_dict[sid][eid], in such a way that
        the first element is the smallest (or recent) of all of the tirps

        :param sid: sequence id
        :param eid: event id
        :param new_tirps: new tirps to be added to self.definitive_ones_indices_dict[sid][eid]
        :return: Nothing. The self.definitive_ones_indices_dict[sid][eid] have been updated
        """

        current_tirps = self.definitive_ones_indices_dict[sid][eid]
        i = 0
        while i < len(new_tirps):
            if new_tirps[i].max_last > current_tirps[0].max_last:
                current_tirps.insert(0, new_tirps[i])
            else:
                current_tirps.append(new_tirps[i])
            i += 1

        self.definitive_ones_indices_dict[sid][eid] = current_tirps

