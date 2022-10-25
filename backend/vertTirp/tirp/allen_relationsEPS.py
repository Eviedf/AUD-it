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
from pandas import Timedelta

MAXGAP = 3155695200

# Trans table based on Mantaining Knowledge about Temporal Intervals
# by James F.Allen
trans_table_0 = dict()
# before b
trans_table_0["bb"] = "b"
trans_table_0["bc"] = "b"
trans_table_0["bo"] = "b"
trans_table_0["bm"] = "b"
trans_table_0["bs"] = "b"
trans_table_0["bf"] = "b"
trans_table_0["be"] = "b"

# equal e
trans_table_0["eb"] = "b"
trans_table_0["ec"] = "c"
trans_table_0["eo"] = "o"
trans_table_0["em"] = "m"
trans_table_0["es"] = "s"
trans_table_0["ef"] = "f"
trans_table_0["ee"] = "e"

# contains c
trans_table_0["cb"] = "bcfmo"
trans_table_0["cc"] = "c"
trans_table_0["co"] = "cfo"
trans_table_0["cm"] = "cfo"
trans_table_0["cs"] = "cfo"
trans_table_0["cf"] = "c"
trans_table_0["ce"] = "c"

# overlaps o
trans_table_0["ob"] = "b"
trans_table_0["oc"] = "bcfmo"
trans_table_0["oo"] = "bmo"
trans_table_0["om"] = "b"
trans_table_0["os"] = "o"
trans_table_0["of"] = "bmo"
trans_table_0["oe"] = "o"

# meets m
trans_table_0["mb"] = "b"
trans_table_0["mc"] = "b"
trans_table_0["mo"] = "b"
trans_table_0["mm"] = "b"
trans_table_0["ms"] = "m"
trans_table_0["mf"] = "b"
trans_table_0["me"] = "m"

# starts s
trans_table_0["sb"] = "b"
trans_table_0["sc"] = "bcfmo"
trans_table_0["so"] = "bmo"
trans_table_0["sm"] = "b"
trans_table_0["ss"] = "s"
trans_table_0["sf"] = "bmo"
trans_table_0["se"] = "s"

# finished-by fi
trans_table_0["fb"] = "b"
trans_table_0["fc"] = "c"
trans_table_0["fo"] = "o"
trans_table_0["fm"] = "m"
trans_table_0["fs"] = "o"
trans_table_0["ff"] = "f"
trans_table_0["fe"] = "f"

##############Trans table based of the vertTIRP article###############
trans_table = dict()
# before b
trans_table["bb"] = "b"
trans_table["bc"] = "b"
trans_table["bo"] = "b"
trans_table["bm"] = "b"
trans_table["bs"] = "b"
trans_table["bf"] = "b"
trans_table["be"] = "b"
trans_table["bl"] = "b"

# contains c
trans_table["cb"] = "bcfmo"
trans_table["cc"] = "c"
trans_table["co"] = "cfo"
trans_table["cm"] = "cfo"
trans_table["cs"] = "cfo"
trans_table["cf"] = "cf"
trans_table["ce"] = "cf"
trans_table["cl"] = "c"

# overlaps o
trans_table["ob"] = "b"
trans_table["oc"] = "bcfmo"
trans_table["oo"] = "bmo"
trans_table["om"] = "bm"
trans_table["os"] = "mo"
trans_table["of"] = "bfmo"
trans_table["oe"] = "mo"
trans_table["ol"] = "cfo"

# meets m
trans_table["mb"] = "b"
trans_table["mc"] = "bm"
trans_table["mo"] = "bm"
trans_table["mm"] = "bm"
trans_table["ms"] = "bm"
trans_table["mf"] = "bm"
trans_table["me"] = "bm"
trans_table["ml"] = "bm"

# starts s
trans_table["sb"] = "b"
trans_table["sc"] = "bcfmo"
trans_table["so"] = "bmo"
trans_table["sm"] = "bm"
trans_table["ss"] = "ms"
trans_table["sf"] = "bmo"
trans_table["se"] = "emos"
trans_table["sl"] = "cflmo"

# finished-by fi
trans_table["fb"] = "bm"
trans_table["fc"] = "cf"
trans_table["fo"] = "fmo"
trans_table["fm"] = "bmo"
trans_table["fs"] = "fmo"
trans_table["ff"] = "cfmo"
trans_table["fe"] = "cflmo"
trans_table["fl"] = "cf"

# equal e
trans_table["eb"] = "bm"
trans_table["ec"] = "cf"
trans_table["eo"] = "fmo"
trans_table["em"] = "bemo"
trans_table["es"] = "eos"
trans_table["ef"] = "cfm"
trans_table["ee"] = "cefo"
trans_table["el"] = "cfl"

# equal l
trans_table["lb"] = "bcfmo"
trans_table["lc"] = "c"
trans_table["lo"] = "cfo"
trans_table["lm"] = "cmo"
trans_table["ls"] = "celo"
trans_table["lf"] = "cf"
trans_table["le"] = "cefl"
trans_table["ll"] = "c"

######################## End trans table ########################

######################## FUNC ESTABLISH GROUPS########################
def get_pairing_strategy(str_rels):
    rels_arr = []
    gr_arr = []

    i = 0
    added = dict()
    while i < len(str_rels):
        c = str_rels[i]
        if (not c in added) and (c == "b"):
            rels_arr.append([c])
            gr_arr.append(None)
            added[c] = True

        elif (not c in added) and (c == "c" or c == "f" or c == "m" or c == "o"):
            gr_arr.append('cfmo')
            if c == "m" or c == "o":
                rels_arr.append([[c]])
                added[c] = True
                j = i + 1

                k = i + 1
                while k < len(str_rels):
                    c = str_rels[k]
                    if not c in added:
                        if c == "m" or c == "o":
                            rels_arr[-1][-1].append(c)
                            added[c] = True
                    k = k + 1

                while j < len(str_rels):
                    c = str_rels[j]
                    if not c in added:
                        if c == "c" or c == "f":
                            rels_arr[-1].append(c)
                            added[c] = True
                    j = j + 1
            else:
                rels_arr.append([c])
                added[c] = True
                j = i + 1

                while j < len(str_rels):
                    c = str_rels[j]
                    if not c in added:
                        if c == "c" or c == "f":
                            rels_arr[-1].append(c)
                            added[c] = True
                        elif c == "m" or c == "o":
                            rels_arr[-1].append([c])
                            added[c] = True
                            k = j + 1
                            while k < len(str_rels):
                                c = str_rels[k]
                                if not c in added:
                                    if c == "m" or c == "o":
                                        rels_arr[-1][-1].append(c)
                                        added[c] = True
                                k = k + 1
                    j = j + 1
        else:
            if not c in added:
                rels_arr.append([c])
                added[c] = True
                gr_arr.append('sel')
                j = i + 1
                while j < len(str_rels):
                    c = str_rels[j]
                    if not c in added:
                        if c == "s" or c == "e" or c == "l":
                            rels_arr[-1].append(c)
                            added[c] = True
                    j = j + 1
        i = i + 1
    return [rels_arr, gr_arr]

######################## END FUNC ESTABLISH GROUPS########################

######################## AUX FUNC ########################

def before_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_s_a_e = ttu(b.start - a.end, time_mode)
    if b_s_a_e > eps:
        if min_gap != 0 and b_s_a_e < min_gap:
            return "1", 1
        elif max_gap != MAXGAP and b_s_a_e > max_gap:
            return "2", 2
        else:
            return "b", 3
    else:
        return "-2", -2


def meets_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_s_a_e = ttu(b.start - a.end, time_mode)
    if abs(b_s_a_e) <= eps:
        return "m", 3
    else:
        return "-2", -2


def overlaps_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_s_a_e = ttu(b.start - a.end, time_mode)
    if b_s_a_e < (-eps):
        return "o", 3
    else:
        return "-2", -2


def contains_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_e_a_e = ttu(b.end - a.end, time_mode)
    if b_e_a_e < (-eps):
        return "c", 3
    else:
        return "-2", -2


def finish_by_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_e_a_e = ttu(b.end - a.end, time_mode)
    if abs(b_e_a_e) <= eps:
        return "f", 3
    else:
        return "-2", -2


def equal_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_e_a_e = ttu(b.end - a.end, time_mode)
    if abs(b_e_a_e) <= eps:
        return "e", 3
    else:
        return "-2", -2


def starts_ind(a, b, eps, min_gap, max_gap, time_mode):
    b_e_a_e = ttu(b.end - a.end, time_mode)
    if b_e_a_e > eps:
        return "s", 3
    else:
        return "-2", -2


def left_contains_ind(a, b, eps, min_gap, max_gap, time_mode):
    if eps == 0:
        return "-2", -2
    b_e_a_e = ttu(b.end - a.end, time_mode)
    if b_e_a_e < (-eps):
        return "l", 3
    else:
        return "-2", -2


def sel_cond(a, b, eps, min_gap, max_gap, time_mode):
    b_s_a_s = ttu(b.start - a.start, time_mode)
    return abs(b_s_a_s) <= eps


def cfmo_cond(a, b, eps, min_gap, max_gap, time_mode):
    b_s_a_s = ttu(b.start - a.start, time_mode)
    return b_s_a_s > eps


def mo_cond(a, b, eps, min_gap, max_gap, time_mode):
    b_e_a_e = ttu(b.end - a.end,time_mode)
    return b_e_a_e > eps


def true_cond(a, b, eps, min_gap, max_gap, time_mode):
    return True


ind_func_dict = dict()
ind_func_dict["b"] = before_ind
ind_func_dict["m"] = meets_ind
ind_func_dict["o"] = overlaps_ind
ind_func_dict["c"] = contains_ind
ind_func_dict["f"] = finish_by_ind
ind_func_dict["e"] = equal_ind
ind_func_dict["s"] = starts_ind
ind_func_dict["l"] = left_contains_ind

cond_dict = dict()
cond_dict["sel"] = sel_cond
cond_dict["cfmo"] = cfmo_cond
cond_dict["mo"] = mo_cond

######################## END AUX FUNC ########################

def ttu(rest_result, time_mode):
    """
    if time_mode is True rest_result should not be converted to seconds, otherwise the rest_result should be
    converted to seconds

    :param rest_result: the result to convert to seconds if necessary
    :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
    :return:
    """
    if time_mode != 2: # modes 1 or 3
        return rest_result
    else:  # mode 2
        return (Timedelta(rest_result)).total_seconds()


class Allen:

    def __init__(self, dummy_calc, trans=True, eps=0):
        self.dummy_calc = dummy_calc
        self.trans = trans
        self.eps = eps


class AllenPairing(Allen):

    def __init__(self, dummy_calc=False, trans=True, eps=0, calc_sort="bselfmoc"):
        super().__init__(dummy_calc, trans, eps)

        self.calc_sort = calc_sort
        [self.rels_arr, self.gr_arr] = get_pairing_strategy(self.calc_sort)

        self.sorted_trans_table = dict()

        if self.eps > 0:
            for key, entry in trans_table.items():
                if len(entry) == 1:
                    self.sorted_trans_table[key] = entry
                else:
                    self.sorted_trans_table[key] = get_pairing_strategy(self.sort_rels(entry))
        else:
            for key, entry in trans_table_0.items():
                if len(entry) == 1:
                    self.sorted_trans_table[key] = entry
                else:
                    self.sorted_trans_table[key] = get_pairing_strategy(self.sort_rels(entry))

    def sort_rels(self, reducted_group):
        reducted_group_sorted = ""
        for ch in self.calc_sort:
            if ch in reducted_group:
                reducted_group_sorted += ch
        return reducted_group

    def calc_rel(self, a, b, eps, min_gap, max_gap, time_mode, rels_arr=None, gr_arr=None):
        """
        calculate and returns the relation name between a and b, and the status. 7 Allen relations are tested.

        :param a: time interval a
        :param b: time interval a
        :param eps: epsilon in seconds or milliseconds according to time_mode, to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :param rels_arr: array of array of relations. eg.:[['l', 'e', 's'], ['b'], [['m', 'o'], 'c', 'f']]
        :param gr_arr: array of array of group conditions ['sel', None, 'cfmo']
        :return: returns the relation name between a and b, and the status
        """

        if not rels_arr:
            rels_arr, gr_arr = self.rels_arr, self.gr_arr

        # if b is less than a
        if b.start < a.start or ((b.start == a.start) and (b.end < a.end)):
            return "1", 1

        for sentence, g in zip(rels_arr, gr_arr):
            if g:
                if cond_dict[g](a, b, eps, min_gap, max_gap, time_mode):  # group cond
                    for words in sentence:
                        if isinstance(words, list):  # mo case
                            if cond_dict["mo"](a, b, eps, min_gap, max_gap, time_mode):
                                for w in words:
                                    r, status = ind_func_dict[w](a, b, eps, min_gap, max_gap, time_mode)  # individual cond
                                    if status > -2:
                                        return r, status
                        else:  # individual conditions
                            r, status = ind_func_dict[words](a, b, eps, min_gap, max_gap, time_mode)  # individual cond
                            if status > -2:
                                return r, status
            else:  # b condition
                r, status = ind_func_dict["b"](a, b, eps, min_gap, max_gap, time_mode)
                if status > -2:
                    return r, status

        return "1", 1

    def get_possible_rels(self, a, b):
        return self.sorted_trans_table[a + b]

    def assign_rel(self, a, b, possible_rels, eps, min_gap, max_gap, time_mode):
        """
        Given the possible relations possible_rels, calculates and returns the relation name between a and b, and the status:
        3 - ok
        2 - max gap restriction
        1 - min gap restriction

        :param a: time interval a
        :param b: time interval a
        :param possible_rels: the possible relations between a and b
        :param eps: epsilon in seconds or milliseconds according to time_mode, to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :return: returns the relation name between a and b, and the status
        """

        if len(possible_rels) == 1:
            first_r = possible_rels[0]
            if first_r == "b":  # Special case with gap
                b_l, b_s = ind_func_dict["b"](a, b, eps, min_gap, max_gap, time_mode)

                if b_s != -2:
                    return b_l, b_s

                return self.calc_rel(a, b, eps, min_gap, max_gap, time_mode)
            else:
                return first_r, 3

        else:
            return self.calc_rel(a, b, eps, min_gap, max_gap, time_mode, possible_rels[0], possible_rels[1])


# ###################### DUMMY AUX FUNCTIONS# ######################

def before(a, b, eps, time_mode, min_gap, max_gap):
    return ind_func_dict["b"](a, b, eps, min_gap, max_gap, time_mode)


def meets(a, b, eps, time_mode, min_gap, max_gap):
    if (abs(ttu(b.start - a.end, time_mode)) <= eps) and (ttu(b.start - a.start,time_mode) > eps) and (ttu(b.end - a.end,time_mode) > eps):
        return "m", 3
    else:
        return "-2", -2


def overlaps(a, b, eps,time_mode, min_gap, max_gap):# KARMA-LEGO AMBIGUOS DEFINITION with contains
    if (ttu(b.start - a.start,time_mode) > eps) and (ttu(b.end - a.end,time_mode) > eps) and (ttu(a.end - b.start, time_mode) > eps):
        return "o", 3
    else:
        return "-2", -2

def contains(a,b,eps, time_mode, min_gap, max_gap):
    if (ttu(b.start - a.start,time_mode) > eps) and (ttu(a.end - b.end,time_mode) > eps):
        return "c", 3
    else:
        return "-2", -2

def finish_by(a,b,eps, time_mode, min_gap, max_gap):
    if (ttu(b.start - a.start,time_mode) > eps) and (abs(ttu(b.end - a.end,time_mode)) <= eps):
        return "f", 3
    else:
        return "-2", -2


def equal(a,b,eps, time_mode, min_gap, max_gap):
    if (abs(ttu(b.start - a.start,time_mode)) <= eps) and (abs(ttu(b.end - a.end,time_mode)) <= eps):
        return "e", 3
    else:
        return "-2", -2


def starts(a,b,eps, time_mode, min_gap, max_gap):
    if (abs(ttu(b.start - a.start,time_mode)) <= eps) and (ttu(b.end - a.end,time_mode) > eps):
        return "s", 3
    else:
        return "-2", -2


def left_contains(a,b,eps, time_mode, min_gap, max_gap):
    if (eps > 0 and abs(ttu(b.start - a.start,time_mode)) <= eps) and (ttu(b.end - a.end,time_mode) < (-eps)):
        return "l", 3
    else:
        return "-2", -2


rel_func_dict = dict()
rel_func_dict["b"] = before
rel_func_dict["m"] = meets
rel_func_dict["o"] = overlaps
rel_func_dict["c"] = contains
rel_func_dict["f"] = finish_by
rel_func_dict["e"] = equal
rel_func_dict["s"] = starts
rel_func_dict["l"] = left_contains

# ###################### END DUMMY AUX FUNCTIONS# ######################

class AllenDummy(Allen):

    def __init__(self, dummy_calc=True, trans=True, eps=0):
        super().__init__(dummy_calc, trans, eps)

    def get_possible_rels(self, a, b):
        if self.eps > 0:
            return trans_table[a + b]
        else:
            return trans_table_0[a + b]

    def calc_rel(self, a, b, eps, min_gap, max_gap, time_mode):
        """
        calculate and returns the relation name between a and b, and the status in a dummy manner

        :param a: time interval a
        :param b: time interval a
        :param eps: epsilon in seconds or milliseconds according to time_mode, to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :return: returns the relation name between a and b, and the status
        """

        # if b is less than a
        if b.start < a.start or ((b.start == a.start) and (b.end < a.end)):
            return "1", 1

        final_rel, final_status = "1", 1  # ini with default values
        for r in ['l','f','s','o','b','c','m','e',]:
            rel, status = rel_func_dict[r](a, b, eps, time_mode, min_gap, max_gap)
            if status != -2:
                final_rel, final_status = rel, status

        return final_rel, final_status

    def assign_rel(self, a, b, possible_rels, eps, min_gap, max_gap, time_mode):
        """
        Given the possible relations possible_rels, calculates and returns the relation name between a and b, and the status:
        3 - ok
        2 - max gap restriction
        1 - min gap restriction

        :param a: time interval a
        :param b: time interval a
        :param possible_rels: the possible relations between a and b
        :param eps: epsilon in seconds or milliseconds according to time_mode, to avoid a crispness in allen relations
        :param min_gap: minimum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param max_gap: maximum gap in seconds allowed between consecutive elements of an occurrence of the sequence
        :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        :return: returns the relation name between a and b, and the status
        """

        if len(possible_rels) == 1:
            first_r = possible_rels[0]
            if first_r == "b":  # Special case with gap
                b_l, b_s = ind_func_dict["b"](a, b, eps, min_gap, max_gap, time_mode)

                if b_s != -2:
                    return b_l, b_s

                return self.calc_rel(a, b, eps, min_gap, max_gap, time_mode)
            else:
                return first_r, 3

        else:
            for r in possible_rels:
                rel, status = rel_func_dict[r](a,b,eps, time_mode, min_gap, max_gap)
                if status != -2:
                    return rel, status

            return self.calc_rel(a, b, eps, min_gap, max_gap, time_mode)
