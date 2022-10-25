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


from numpy import mean

__slots__ = ['time_mode', 'sequence_events_tirps_dict', 'sum_ver_supp', 'sum_hor_per_seq', 'last_modified',
             'sum_mean_duration','n_instances_per_seq','mean_duration']
class TIRPstatistics:
    """
    This class is designed to store sidlist indicators, such as a vertical and horizontal supports,
    and a mean duration of a given TIRP
    """
    def __init__(self, time_mode=True):

        #   1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
        self.time_mode = time_mode

        # USEFUL TO LOCALIZE A TIRP IN THE sidlist array in a faster manner
        # a dict where key is a sequence id
        # and value is a dict where key is event id and value is a TIRP array
        self.sequence_events_tirps_dict = dict()

        # vertical support, i.e. number of sequences having the pattern p
        self.sum_ver_supp = 0

        # horizontal support per sequence, i.e. sum of all instances that have p in sequence s1
        self.sum_hor_per_seq = dict()

        # MEAN DURATION VARS
        # last sequence where the TIRP appears
        # necessary to know when we changed the sequence
        self.last_modified = -1
        # a vector of sums of mean durations of sequences
        self.sum_mean_duration = []
        # a vector of number of instances by sequence
        self.n_instances_per_seq = []
        self.mean_duration = []

    def append_tirp(self, seq_id, eid, tirp):
        """
        Appends a tirp, and
        modifies sum_ver_supp, sum_hor_per_seq, and the duration variables
        :param seq_id: sequence id
        :param eid: event id
        :param tirp: tirp to add
        :return: Appends a tirp
        """
        if seq_id in self.sequence_events_tirps_dict:

            if not eid in self.sequence_events_tirps_dict[seq_id]:
                self.sequence_events_tirps_dict[seq_id][eid] = []

            self.sequence_events_tirps_dict[seq_id][eid].append(tirp)

            self.sum_mean_duration[-1] += tirp.get_duration(self.time_mode)
            self.n_instances_per_seq[-1] += 1
        else:
            # if self.last_modified != -1:  # change of sequence
            #     # we can calculate the mean duration of the previous one
            #     self.mean_duration.append(self.sum_mean_duration[-1]/self.n_instances_per_seq[-1])

            self.sum_mean_duration.append(tirp.get_duration(self.time_mode))
            self.n_instances_per_seq.append(1)

            self.sequence_events_tirps_dict[seq_id] = dict()
            self.sequence_events_tirps_dict[seq_id][eid] = [tirp]
            self.sum_ver_supp += 1

            # initialize hor support for sequence
            self.sum_hor_per_seq[seq_id] = 0

        self.last_modified = seq_id
        self.sum_hor_per_seq[seq_id] += 1
        return self.sum_ver_supp

    def get_mean_hor_support(self, events_per_sequence):
        """
        :param events_per_sequence: a dictionary where key is a sequence id and value is number of items in sequence
        returns the horizontal support that is self.sum_hor_per_seq / self.sum_ver_supp
        :return: returns the horizontal support that is self.sum_hor_per_seq / self.sum_ver_supp
        """
        rel_sum = 0.0
        for sid, sumv in self.sum_hor_per_seq.items():
            rel_sum += sumv/events_per_sequence[sid]

        return rel_sum / self.sum_ver_supp

    def get_ver_support(self, n_sequences):
        """
        returns the vertical relative support
        :param n_sequences: total number of sequences
        :return: returns the vertical relative support
        """
        return self.sum_ver_supp / n_sequences

    def get_mean_duration(self):
        """
        Returns the mean duration vector, where each event id represents a sequence
        :return: returns the mean duration vector, where each event id represents a sequence
        """
        # append the last mean_duration that have not been added yet
        if self.last_modified != -1:  # not empty sequence
            for sum, n_inst in zip(self.sum_mean_duration, self.n_instances_per_seq):
                # we can calculate the mean duration of the previous one
                self.mean_duration.append(sum/n_inst)

            return self.mean_duration
        else:  # empty sequence
            return [0]

    def get_mean_of_means_duration(self, units="hours"):
        """
                returns the overall mean
                :param: units: seconds, minutes, hours, days, weeks, years
                :return: returns the overall mean
                """
        if self.time_mode == 1 or self.time_mode == 2:
            switcher = {"seconds": 1, "minutes": 60, "hours": 60 * 60,
                        "days": 60 * 60 * 24, "weeks": 60 * 60 * 24 * 7,
                        "years": 60 * 60 * 24 * 365}
            return str(mean(self.get_mean_duration()) / switcher.get(units, 1)) + " " + units
        else:
            return str(mean(self.get_mean_duration()))
