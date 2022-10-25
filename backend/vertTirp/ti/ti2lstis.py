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


import pandas as pd
# from ti.ti import LinkedList, TI_node
from vertTirp.ti.ti import LinkedList, TI_node
import datetime


class DT:
    """ DT is a datetime class, used in the map function, where format can not be assigned"""
    def __init__(self,date_format="%Y-%m-%d %H:%M:%S"):
        self.date_format = date_format

    def apply_strptime(self,x):
        return datetime.datetime.strptime(x, self.date_format)

def ti_read(df, seqid_column = "sid", date_column_name_start = "start_time", date_column_name_end = "end_time", date_format = "%Y/%m/%d %H:%M:%S", val_column_names = ['value'],
            is_null_f=pd.isna, time_mode=1):
    """
    Converts time interval data to time intervals grouped by sequence and sorted lexicographically.

    :param filepath: Any valid string path is acceptable
    :param sep: delimiter to use with the scv file
    :param seqid_column: sequence column name
    :param date_column_name_start: start date or timestamp column name
    :param date_column_name_end: end date or timestamp column name
    :param date_format: format of the date
    :param val_column_names: a list of value column names
    :param is_null_f: function name to evaluate null values
    :param time_mode: 1- timestamp mode, 2- datetime mode 3- number mode(e.g. number of frame)
    :param out_file: output file name
    :return: a list of time intervals by sequence sorted lexicographically,
    where each position represents a different sequence. And an array with the sequence names, where
    each position corresponds to the position of the list of time intervals
    """

    grouped_by_uid = df.groupby(seqid_column)
    l_of_ti_sequences = []
    l_of_sequences = []

    ti_count = 0

    for uid, df_gr in grouped_by_uid:
        ti = ti_to_list(df_gr, date_column_name_start, date_column_name_end, date_format, val_column_names, is_null_f, time_mode)
        if ti:
            l_of_sequences.append(uid)
            l_of_ti_sequences.append(ti)
            ti_count += ti[0].size

    return l_of_ti_sequences, l_of_sequences, ti_count


def ti_to_list(df, date_column_name_start, date_column_name_end, date_format, val_column_names, is_null_f=pd.isna, time_mode=1):

    """
    Converts a dataframe into a list of time intervals sorted lexicographically

    :param df: dataframe
    :param date_column_name_start: start date or timestamp column name
    :param date_column_name_end: end date or timestamp column name
    :param date_format: format of the date
    :param val_column_names: a list of value column names
    :param is_null_f: function name to evaluate null values
    :param time_mode: 1- timestamp mode in seconds, 2- datetime mode 3- number mode(e.g. number of frame)
    :return: a list of time intervals sorted lexicographically
    """

    if df.shape[0] < 2:
        return []

    if time_mode == 1:  # timestamp
        dt_obj = DT(date_format)
        timestamp_array_start = map(dt_obj.apply_strptime, df[date_column_name_start].values)
        timestamp_array_end = map(dt_obj.apply_strptime, df[date_column_name_end].values)

        timestamp_array_start = [datetime.datetime.timestamp(r) for r in timestamp_array_start]
        timestamp_array_end = [datetime.datetime.timestamp(r) for r in timestamp_array_end]

    elif time_mode == 2:  # pandas datetime
        timestamp_array_start = pd.to_datetime(df[date_column_name_start].values, format=date_format).values
        timestamp_array_end = pd.to_datetime(df[date_column_name_end].values, format=date_format).values

    else:  # number mode
        timestamp_array_start = df[date_column_name_start].values
        timestamp_array_end = df[date_column_name_end].values

    list_of_ti = LinkedList()
    for val_column_name in val_column_names:
        list_of_ti = sorted_insert_attr(df[val_column_name].values, val_column_name, timestamp_array_start, timestamp_array_end, list_of_ti, is_null_f)

    return [list_of_ti]


def sorted_insert_attr(series, attr_name, timestamp_array_start, timestamp_array_end, list_of_ti, is_null_f=pd.isna):

    """
    Inserts an attribute (of type series) into a list of time intervals (list_of_ti) in a sorted manner

    :param series: an attribute to insert
    :param attr_name: an attribute name
    :param timestamp_array_start: start date or timestamp column name
    :param timestamp_array_end: end date or timestamp column name
    :param list_of_ti: a list of time intervals where the attribute will be inserted
    :param is_null_f: function name to evaluate null values
    :return: a list of time intervals sorted lexicographically
    """

    attr_name = attr_name + '_'
    current_node = None
    last_node = current_node

    series_size = len(series)
    for i in range(series_size):
        if not is_null_f(series[i]):
            current_sym = attr_name + str(series[i])
            current_node = TI_node(current_sym, timestamp_array_start[i], timestamp_array_end[i])
            list_of_ti.sortedInsert(current_node, last_node)
            last_node = current_node

    return list_of_ti


