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
from vertTirp.ti.ti import TI
from pandas import Timedelta
from vertTirp.tirp.allen_relationsEPS import ttu

__slots__ = ['ti', 'r', 'first', 'max_last']
class TIRP:

    # Constructor to initialize a time interval related pattern or TIRP

    def __init__(self, ti, first, max_last, r=None):
        self.ti = ti  # [ti] a list of time intervals list sorted lexicographically
        # where each ti is a TI object with a corresponding start, end and sym

        if not r:
            r = []

        self.r = r  # relation list between all the items, as in the Karma-Lego algorithm

        self.first = first  # first of all the symbols time, the first of firsts
        self.max_last = max_last  # latest end_time of all the symbols the max_last

    def my_copy(self):
        """
        Performs a deep copy of self
        :return: a deep copy of self
        """
        new_r = [i for i in self.r]

        # shallow copy
        # new_ti = self.ti[:]

        # deep copy
        new_ti = [TI(t.sym, t.start, t.end) for t in self.ti]
        return TIRP(new_ti, self.first, self.max_last, new_r)

    def __lt__(self, tirp):
        """
        returns True id self < tirp, False otherwise
        :param tirp: another tirp
        :return: returns True id self < tirp, False otherwise
        """
        if self.first < tirp.first:
            return True
        else:
            if self.first == tirp.first:
                return self.max_last < tirp.max_last
            else:  # self.ti.first > node.ti.first:
                return False

    def __le__(self, tirp):
        """
        returns True id self <= tirp, False otherwise
        :param tirp: another tirp
        :return: returns True id self <= tirp, False otherwise
        """
        if self.first < tirp.first:
            return True
        else:
            if self.first == tirp.first:
                return (self.max_last < tirp.max_last) or (self.max_last == tirp.max_last)
            else:  # self.ti.first > node.ti.first:
                return False

    def get_rel_as_str(self):
        """
        returns relation as string
        :return: returns relation as string
        """
        return "".join(str(x) for x in self.r)

    def get_duration(self, time_mode=True):
        """
        returns the duration of the tirp
        :param time_mode:  1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :return:  returns the duration of the tirp
        """
        if time_mode != 2: # time_mode== 1 or 3
            return self.max_last - self.first
        else:  # time_mode== 2
            return (Timedelta(self.max_last - self.first)).total_seconds()

    def extend_with(self, s_ti, eps, min_gap, max_gap, max_duration, time_mode, mine_last_equal, allen):
        """
        If max gap or min gap met, returns None, and the status, otherwise returns the extended TIRP and the status.
        Performs the extension with an allen's transitivity properties and epsilon to avoid crisp borders

        :param s_ti: time interval to extend with
        :param eps: an epsilon to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_duration: maximum duration in seconds of a tirp
        :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :param mine_last_equal: whether to mine tirp with the last equal relation
        :return: if max gap exceeded, returns None, and the status, otherwise returns the extended TIRP and the status
        """

        # calc and assign the last relation
        c_rel, status_rel = allen.calc_rel(self.ti[-1], s_ti, eps, min_gap, max_gap, time_mode)

        # the s-extension case
        if not mine_last_equal and c_rel == "e":
            return None, 1

        if status_rel < 3:
            # max gap or min gaps exceeded
            return None, status_rel

        # ini new relation
        new_rel = [nr for nr in self.r]
        new_rel.extend([""] * len(self.ti))

        new_rel[-1] = c_rel

        # copy if self.ti
        new_ti = [TI(n.sym, n.start, n.end) for n in self.ti]
        # appends s_ti
        new_ti.append(s_ti)

        # determine the maximum end time
        new_max_last = s_ti.end
        if new_max_last < self.max_last:
            new_max_last = self.max_last

        # max duration constraint
        if ttu(new_max_last-self.first, time_mode) > max_duration:
            return None, 1

        size_rel = len(new_rel)
        size_sym = len(new_ti)

        r_idx = 1
        temp = size_sym - r_idx
        first_pos = int(((temp ** 2 - temp) / 2) - 1)
        while first_pos >= 0:
            second_pos = size_rel - r_idx
            pos_to_assign = second_pos - 1
            existent_node = new_ti[temp - 2]
            if allen.trans:
                possible_rels = allen.get_possible_rels(new_rel[first_pos], new_rel[second_pos])
                c_rel, status_rel = allen.assign_rel(existent_node, s_ti, possible_rels, eps, min_gap, max_gap, time_mode)
            else:
                # calc and assign the last relation
                c_rel, status_rel = allen.calc_rel(existent_node, s_ti, eps, min_gap, max_gap, time_mode)

            if status_rel < 3:
                # max gap or min gaps exceeded
                return None, status_rel

            # assigns the relation to the position
            new_rel[pos_to_assign] = c_rel

            r_idx += 1
            temp = size_sym - r_idx
            first_pos = int(((temp ** 2 - temp) / 2) - 1)

        return (TIRP(new_ti, new_ti[0].start, new_max_last, new_rel)), 3
