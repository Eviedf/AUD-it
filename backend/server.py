from functools import lru_cache
from select import select
from unittest import FunctionTestCase
from flask import Flask, make_response, request, send_from_directory, jsonify
import json
from jinja2 import select_autoescape
import pandas as pd
from flask_cors import CORS
import numpy as np
import json
from datetime import datetime, timezone, tzinfo, time, timedelta, date
from pandas import Series
from dateutil import tz
import ast
from hashlib import md5
import pytz
import time
import os
from vertTirp.ti.ti2lstis import ti_read
from vertTirp.vertTirp import VertTIRP
import re
import itertools
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import complete, dendrogram, cut_tree
from matplotlib import pyplot as plt
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import pdist, jaccard, squareform
from yellowbrick.cluster import KElbowVisualizer
from scipy.cluster.hierarchy import ClusterWarning
from warnings import simplefilter
simplefilter("ignore", ClusterWarning)

pd.options.mode.chained_assignment = None
np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)   


app = Flask(__name__)
CORS(app)

#######################################################
# User-defined parameters
########################################################

# select data directory: "dummydata/datasets for dummydata"
data_directory = "data/datasets"
events = [
        'connectivity',
        'light_lux',
        'notification',
        'powerState',
        'usage',
        'sms',
        'activity',
        'call',
        'proximity',
        'acceleration'
    ]

# list the attributes per event name
def get_attributes(event):
    if event == 'connectivity':
        attributes = ['wifi', 'offline', 'cellular']
    elif event == 'light_lux' or event == 'acceleration':
        attributes = ['low',  'medium',  'high']
    elif event == 'notification':
        attributes = ['post_facebook', 'remove_facebook', 'post_whatsapp',
                      'remove_whatsapp', "post_prosit", "remove_prosit"]
    elif event == 'powerState':
        attributes = ['screen_on', 'screen_off', 'power_connected', 'shutdown', 'boot_completed',
                      'airplane_mode_changed']
    elif event == 'usage':
        attributes = ['to_foreground', 'start_screen_non_interactive', 'start_keyguard_shown',
                      'start_screen_interactive', 'start_keyguard_hidden',
                      'start_foreground_service', 'stop_foreground_service']
    elif event == 'sms':
        attributes = ['inbox', 'sent']
    elif event == 'activity':
        attributes = [
            'still', 'tilting', 'unknown', 'inVehicle', 'onFoot', 'onBycicle']
    elif event == 'call':
        attributes = ['outgoing_start', 'outgoing_end', 'incoming_start', 'incoming_end']
    elif event == 'proximity':
        attributes = ['close', 'far']
    else:
        attributes = ["0", "1", "2", "3"]
    return attributes

############################################################
# Backend functions     
############################################################

# concatenate intervaldfs for each selected user and append duration column
@lru_cache
def get_intervaldata(set):
    set = set.split(',')
    final_df = pd.DataFrame(columns=['sid', 'start_time', 'end_time', 'value'])
    for id in set:
        path = data_directory + '/' + id + '/intervaldata.pickle'
        isExists = os.path.exists(path)
        if isExists:
            df = pd.read_pickle(path)
            final_df = pd.concat([final_df, df])
    final_df['event'] = final_df['value'].str.split("/", expand=True)[0]
    # final_df = final_df[final_df['event'].isin(events)]
    final_df = final_df.reset_index(drop=True)
    final_df['eid'] = final_df.index
    final_df['start_time'] =  pd.to_datetime(final_df['start_time'], utc=True)
    final_df['end_time'] =  pd.to_datetime(final_df['end_time'], utc=True)
    final_df['duration'] = (final_df['end_time'] - final_df['start_time']).astype('timedelta64[m]')
    return final_df

# filter the intervaldata on selected intervals
def filter_intervaldata(df, selected_intervals):
    selected_intervals = json.loads(selected_intervals)
    filter_intervals = [x.replace("-", "/") for x in selected_intervals]
    final_df = df[df['value'].isin(filter_intervals)]
    return final_df

# create daily sequences, intervals that happen on two days are split up into two separate intervals
def bin_intervals_byday(df):
    df = df.reset_index(drop=True)
    df['participant_id'] = df['sid']
    indices = df.index[df['end_time'].dt.strftime('%Y/%m/%d') != df['start_time'].dt.strftime('%Y/%m/%d')].tolist()
    for i in indices:
        first = df['start_time'][i].strftime('%Y/%m/%d')
        second = df['end_time'][i].strftime('%Y/%m/%d')
        row = df.iloc[i].tolist()
        row[1] = pd.to_datetime((second + " 00:01"), utc=False)
        df.loc[len(df)] = row
        df.iloc[i, df.columns.get_loc('end_time')] = pd.to_datetime((first + " 23:59"), utc=False)

    df['start_time'] =  pd.to_datetime(df['start_time'], utc=True)
    df['end_time'] =  pd.to_datetime(df['end_time'], utc=True)
    df['timebin'] = df['start_time'].dt.strftime('%Y/%m/%d')
    df['sid'] = pd.factorize(df.timebin+df.sid)[0]
    df['summeddurx'] = df.groupby(by=['sid', 'value'])['duration'].transform('sum')

    return df

# creates sequences for selected intervals based on the selected timeframe and durations
@lru_cache
def bin_intervals_custom(set, selected_intervals, selected_durs, selectedhours):
    print("Binning")
    rawdf = get_intervaldata(set)
    rawdf = filter_intervaldata(rawdf, selected_intervals)
    selecteddurs = json.loads(selected_durs)
    if selectedhours != "undefined":
        selectedhours = selectedhours.split(',')

        # sometimes the hour selection returns negative floats, if this happens, these are converted into the positive variant
        if float(selectedhours[0]) < 0:
            selectedhours[0] = 24 + float(selectedhours[0])
        if float(selectedhours[1]) < 0:
            selectedhours[1] = 24 + float(selectedhours[1])

        # convert hour floats into timedelta
        firsthour = timedelta(hours = float(selectedhours[0]))
        secondhour = timedelta(hours = float(selectedhours[1]))
    else: 
        firsthour = timedelta(hours=0)
        secondhour = timedelta(hours=24)

    # filter the dataframe on selected durations, if no duration is selected for a selected interval, include all durations
    for key in selecteddurs:
        interval = key.replace("-", "/")
        durations = selecteddurs[key]
        intervaldf = rawdf.loc[rawdf['value'] == interval]
        intervaldf = intervaldf.loc[(float(durations[0]) <= intervaldf['duration'].astype(float)) & (intervaldf['duration'].astype(float) <= float(durations[1]))]
        rawdf = rawdf.loc[rawdf['value'] != interval]
        rawdf = pd.concat([rawdf, intervaldf])

    duration = secondhour - firsthour
    if duration.days != 0:
        firstday = rawdf.loc[rawdf['start_time'] >= rawdf['start_time'].dt.normalize() + firsthour]
        secondday = rawdf.loc[rawdf['start_time'] <= rawdf['start_time'].dt.normalize() + firsthour]

        leftoverlap = rawdf.loc[(rawdf['start_time'] <= rawdf['start_time'].dt.normalize() + firsthour) & (rawdf['end_time'] <= rawdf['start_time'].dt.normalize()  + timedelta(days=1) + secondhour) & (rawdf['end_time'] >= rawdf['start_time'].dt.normalize() + firsthour)]
        # convert the interval times to be cut off at the selected hours boundaries
        leftoverlap['start_time'] = leftoverlap['start_time'].dt.normalize() + firsthour


        right_first = firstday.loc[(firstday['start_time'] <= firstday['start_time'].dt.normalize() + secondhour + timedelta(days=1)) & (firstday['start_time'] >= firstday['start_time'].dt.normalize() + firsthour) & (firstday['end_time'] >= firstday['start_time'].dt.normalize() + secondhour + timedelta(days=1))]
        right_first['end_time'] = right_first['start_time'].dt.normalize() + secondhour + timedelta(days=1)
        right_second = secondday.loc[(secondday['start_time'] <= secondday['start_time'].dt.normalize() + secondhour) & (secondday['start_time'] >= secondday['start_time'].dt.normalize() - timedelta(days=1) + firsthour) & (secondday['end_time'] >= secondday['start_time'].dt.normalize() + secondhour)]
        right_second['end_time'] = right_second['start_time'].dt.normalize() + secondhour
        rightoverlap = pd.concat([right_first, right_second])

        middle_first =  firstday.loc[(firstday['start_time'] >= firstday['start_time'].dt.normalize() + firsthour) & (firstday['end_time'] <= firstday['start_time'].dt.normalize() + secondhour + timedelta(days=1))]
        middle_second = secondday.loc[(secondday['start_time'] >= secondday['start_time'].dt.normalize() + firsthour - timedelta(days=1)) & (secondday['end_time'] <= secondday['start_time'].dt.normalize() + secondhour)]
        middle = pd.concat([middle_first, middle_second])

        fulloverlap = rawdf.loc[(rawdf['start_time'] <= rawdf['start_time'].dt.normalize() + firsthour) & (rawdf['end_time'] >= rawdf['start_time'].dt.normalize() + secondhour + timedelta(days=1))]
        fulloverlap['start_time'] = fulloverlap['start_time'].dt.normalize() + firsthour
        fulloverlap['end_time'] = fulloverlap['start_time'].dt.normalize() + secondhour + timedelta(days=1)

    else:
        # compute all intervals where start_time is smaller than the first selected hour and end_time is smaller than the second selected hour
        leftoverlap = rawdf.loc[(rawdf['start_time'] <= rawdf['end_time'].dt.normalize() + firsthour) & (rawdf['end_time'] <= rawdf['end_time'].dt.normalize() + secondhour) & (rawdf['end_time'] >= rawdf['end_time'].dt.normalize() + firsthour)]

        # compute al intervals where start_time is bigger than the first selected hour and end_time is bigger than the second selected hour
        rightoverlap = rawdf.loc[(rawdf['start_time'] >= rawdf['start_time'].dt.normalize() + firsthour) & (rawdf['end_time'] >= rawdf['start_time'].dt.normalize() + secondhour) & (rawdf['start_time'] <= rawdf['start_time'].dt.normalize() + secondhour)]

        # compute all intervals that are inbetween the selected hours
        middle = rawdf.loc[(rawdf['start_time'] >= rawdf['start_time'].dt.normalize() + firsthour) & (rawdf['end_time'] <=  rawdf['start_time'].dt.normalize() + secondhour)]

        # compute all intervals containing both selected times
        fulloverlap = rawdf.loc[(rawdf['start_time'] <= rawdf['end_time'].dt.normalize() + firsthour) & (rawdf['end_time'] >= rawdf['end_time'].dt.normalize() + secondhour)]

        # convert the interval times to be cut off at the selected hours boundaries
        leftoverlap['start_time'] = leftoverlap['end_time'].dt.normalize() + firsthour
        rightoverlap['end_time'] = rightoverlap['start_time'].dt.normalize() + secondhour
        fulloverlap['start_time'] = fulloverlap['end_time'].dt.normalize() + firsthour
        fulloverlap['end_time'] = fulloverlap['end_time'].dt.normalize() + secondhour
    filtereddf = pd.concat([leftoverlap, rightoverlap, middle, fulloverlap]).drop_duplicates()
    filtereddf['duration'] = (filtereddf['end_time'] - filtereddf['start_time']).astype('timedelta64[m]')


    # if the selected timeframe covers two consecutive days, create sequence ids based on timeframe and user id
    if duration.days != 0:
        duration = duration - timedelta(days=duration.days)
        filtereddf = filtereddf.sort_values(['sid', 'start_time']).reset_index(drop=True)
        binned_df = pd.DataFrame(columns=['sid', 'start_time', 'end_time', 'value', 'duration', 'timebin'])
        ids = filtereddf['sid'].unique()
        id = 0
        for i in range(len(ids)):
            id_df = filtereddf.loc[filtereddf['sid'] == ids[i]]
            while len(id_df) > 0:
                date1 = id_df.iloc[0]['start_time'].strftime('%Y/%m/%d')
                date2 = id_df.iloc[0]['end_time'].strftime('%Y/%m/%d')
                if date1 == date2:
                    if (datetime.min + firsthour).time() > id_df.iloc[0]['start_time'].time():
                        start = id_df.iloc[0]['start_time'].normalize() - timedelta(days=1) + firsthour
                    else:
                        start = id_df.iloc[0]['start_time'].normalize() + firsthour
                else: 
                    start = id_df.iloc[0]['start_time'].normalize() + firsthour
                end = start + duration
                bin_df = id_df.loc[(start <= id_df['start_time']) & (id_df['start_time'] <= end)]
                id_df = id_df.drop(bin_df.index)
                bin_df['part'] = bin_df['sid']
                bin_df['sid'] = id
                binned_df = pd.concat([binned_df, bin_df])
                id += 1
        binned_df = binned_df.sort_values('value')
    # if selected timeframe only includes times on the same day, create sequence ids based on date and user id
    else:
        binned_df = filtereddf
        binned_df['timebin'] = binned_df['start_time'].dt.strftime('%Y/%m/%d')
        binned_df['sid'] = pd.factorize(binned_df.timebin+binned_df.sid)[0]
        binned_df = binned_df.drop(columns=['timebin'])
    return binned_df

# mine patterns according to the VERTIRP algorithm: https://doi.org/10.1016/j.eswa.2020.114276 
# (Mordvanyuk, N., López, B., & Bifet, A. (2021). vertTIRP: Robust and efficient vertical frequent time interval-related pattern mining. Expert Systems with Applications, 168, 114276.)
def mine_seqs(df):
    df = df.reset_index(drop=True)
    
    # ensure that start and endtime are in string format
    df['start_time'] =  pd.to_datetime(df['start_time'], utc=False)
    df['end_time'] =  pd.to_datetime(df['end_time'], utc=False)

    df = df.sort_values(by=['start_time', 'end_time']).reset_index(drop=True)
    df['start_time'] = df['start_time'].dt.strftime('%Y/%m/%d %H:%M:%S')
    df['end_time'] = df['end_time'].dt.strftime('%Y/%m/%d %H:%M:%S')
    df = df.drop(columns='eid')

    # parameters explanation
    timestamp_mode = 1  # timestamp_mode: if True we convert the date to timestamp (long number), otherwise to datetime.
    ver_sup = 0.05 # vertical support
    eps = 0  # epsilon value in seconds, that allows uncertainty and avoids crisp borders in relations
    dummy = False  # whether to execute relations without a pairing strategies
    trans = True  # whether to use transitivity properties when assign a relation
    result_file_name = "my_result_file.csv"  # an output file 

    avoid_same_var_states = False
    ming = 0 # minimum gap in seconds that is the gap between before consecutive elements
    # change this to a lower number if processing takes too long..
    maxg = 30 # maximum gap in seconds that is the gap between before consecutive elements
    mind = 1 # each event interval should have a duration of at least min_duration seconds
    maxd = 60*60*10  # each tirp should have a duration of at most min_duration seconds
    # ps is a string that represents relations sorted and grouped following a pairing strategy
    # If None, a default common strategies will be used that is:
    # "bmocfse" for eps = 0, and "bselfmoc" for eps>0
    ps = "mocfbes"

    # reads time intervals from csv and transforms them to the LSTIs representation
    list_of_ti_users, list_of_users, ti_count = ti_read(df)

    # initialize the algorithm with parameters
    co = VertTIRP(time_mode=timestamp_mode, out_file=result_file_name, min_sup_rel=ver_sup,
                eps=eps, min_gap=ming, max_gap=maxg, min_duration=mind, max_duration=maxd, dummy_calc=dummy,
                ps=ps, trans=trans)
    # constructs a vertical dataset representation and mines the patterns
    # mine_patterns corresponds to the vertTIRP algorithm from the article
    tirp_count = co.mine_patterns(list_of_ti_users, list_of_users, avoid_same_var_states)
    print(tirp_count)
    # prints the tirps in the deep first search fashion if dfs=True,
    # and in breast first search if dfs=False
    co.print_patterns(dfs=True)


# retrieve pandas dataframe with pattern relative times and support metrics from VERTIRP csv file ("my_result_file.csv")
def format_patterns():
    ruledf = pd.DataFrame(columns=('pattern_id', 'relations', 'interval', 'times', 'support')).astype(object)
    with open("my_result_file.csv") as f:
        pattern_id = 0
        lines = f.readlines()
        i = 0
        # loop over the lines in the csv file
        while i <= len(lines) - 1:
            # retrieve line1, which contains the event-interval names for a pattern
            line1 = lines[i].strip()
            line1 = eval(line1)
            # filter patterns with more than one event
            if len(line1) > 1:
                count = 1
                for k, line2 in enumerate(lines[i+1:]):
                    if "#" in line2:
                        # retrieve line2, which contains the pattern type, the vertical and horizontal support and the mean duration
                        # note: line1 can be accompanied by multiple line2's
                        relations =  re.split("#", line2)
                        symseq = relations[0].strip()
                        if len(symseq) < 3:
                            supp = relations[1].split("ver:")[1].strip()
                            relations = relations[0].strip()
                            timelist = pd.DataFrame(columns=('pattern_id', 'relations', 'interval', 'times', 'support')).astype(object)

                        # loop over the length of the relation types 
                            for j in range(len(line1)):
                                element = line1[j]
                                nr_relations = len(line1[j+1:])
                                elementlist = re.split('value_', element)
                                interval = elementlist[1]
                                # transformations from relation type to relative times, will be used to visualize the intervals as rectangles on a relative timeline
                                # the first element gets timestamps 0 and 1
                                if j == 0:
                                    times = [0, 1]
                                    timelist.loc[len(timelist)] = [pattern_id, symseq, interval, times, supp]
                                for l in range(nr_relations):
                                    interval = re.split('value_', line1[j + l + 1])[1]
                                    relation = relations[l] 
                                    if relation == 'b':
                                        times = [timelist.iloc[j]['times'][0] + 2, timelist.iloc[j ]['times'][1] + 2]
                                    elif relation == 'm':
                                        times = [timelist.iloc[j]['times'][1], timelist.iloc[j]['times'][1] + 1]
                                    elif relation == 'c':
                                        times = [timelist.iloc[j]['times'][0] + 1/4, timelist.iloc[j]['times'][1] - 1/4]
                                    elif relation == 'o':
                                        times = [timelist.iloc[j]['times'][1] - 1/4, timelist.iloc[j]['times'][1] + 3/4]
                                    elif relation == 'f':
                                        times = [timelist.iloc[j]['times'][0] + 1/4, timelist.iloc[j]['times'][1]]
                                    elif relation == 'e':
                                        times = [timelist.iloc[j]['times'][0], timelist.iloc[j]['times'][1]]
                                    elif relation == 's':
                                        timelist.loc[j, 'times'] = [[timelist.iloc[j]['times'][0]], [timelist.iloc[j]['times'][0] + 1/2]]
                                        times = [timelist.iloc[j]['times'][0], timelist.iloc[j]['times'][0] + 1]
                                    timelist.loc[l + j + 1] = [pattern_id, symseq, interval, times, supp]
                                relations = relations[nr_relations:]
                            ruledf = pd.concat([ruledf, timelist])
                            pattern_id += 1
                        count +=1
                    else:
                        i += count
                        break  
                if k == len(lines[i+1:]) -1:
                    i = len(lines) + 1
            else:
                i += 2  
    ruledf['id'] = ruledf.index
    return ruledf

# function to round time
def roundTime(dt=None, roundTo=60):
   """Round a datetime object to any time lapse in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
   if dt == None : dt = datetime.now()
   seconds = (dt.replace(tzinfo=None) - dt.min).seconds
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + timedelta(0,rounding-seconds,-dt.microsecond)


# following https://towardsdatascience.com/how-to-apply-hierarchical-clustering-to-time-series-a5fe2a7d8447
def radial_cluster(data):
    intervals = data['value'].unique()

    # transform intervaldataframe into dataframe that contains binary time vectors, taking time steps of 'min_gap' in minutes
    start = datetime.strptime("00:00:00", "%H:%M:%S")
    end = datetime.strptime("23:59:00", "%H:%M:%S")
    min_gap = 5
    time_array = np.array([(start + timedelta(hours=min_gap*i/60)).time() for i in range(int((end-start).total_seconds() / 60.0 / min_gap) + 1)])

    ordereddata = pd.DataFrame()
    for interval in intervals:
        intervaldata = data.loc[data['value'] == interval]
        ids = intervaldata['sid'].unique()

        clusterdf = []
        durations = []
        for id in ids:
            seqdf = intervaldata.loc[intervaldata['sid'] == id]
            summeddur = seqdf['duration'].sum()
            durations.append(summeddur)
            date = seqdf.iloc[0]['start_time'].date()
            sid_time_array = np.array([datetime.combine(date, x) for x in time_array])
            # round start_time and end_time to nearest 5 minute timestamp
            seqdf['start_time'] = seqdf['start_time'].apply(lambda x: roundTime(x.to_pydatetime().replace(tzinfo=None), roundTo=60*5))
            seqdf['end_time'] = seqdf['end_time'].apply(lambda x: roundTime(x.to_pydatetime().replace(tzinfo=None), roundTo=60*5))
            seqdf['end_time'] = seqdf['end_time'].apply(lambda x: roundTime(x.to_pydatetime().replace(tzinfo=None), roundTo=60*5))
            indiceslist = np.array([])
            for index, row in seqdf.iterrows():
                indices = np.where((sid_time_array >= row['start_time']) & (sid_time_array <= row['end_time']))[0]
                indiceslist = np.append(indiceslist, indices)
            vector = np.zeros(len(time_array))
            vector[indices] = 1
            clusterdf.append(vector)
        if len(clusterdf) > 5:
            # compute distance matrix based on Jaccard distance
            distances = pdist(clusterdf, 'jaccard')
            distancematrix = squareform(distances)
            linkage_matrix =  complete(distancematrix)

            color_threshold = 0.7 * max(linkage_matrix[:, 2])
            n_color = len(np.unique(cut_tree(linkage_matrix, height = color_threshold)))
            if n_color > 5:
                n_color = 1
            dn = dendrogram(linkage_matrix)

            plt.figure(figsize=(25, 10))
            dendrogram(linkage_matrix)
            plt.savefig("dendrogram.png")
            plt.show()


            #select number of clusters based on elbow method
            # model = AgglomerativeClustering(affinity='precomputed', linkage='complete')
            # visualizer = KElbowVisualizer(model, k=(1, 5))
            # visualizer.fit(distancematrix)
            # visualizer.show()
            # nr_clusters = visualizer.elbow_value_
            # if nr_clusters == None:
            #     nr_clusters = 1

            cluster_labels = fcluster(linkage_matrix, n_color, criterion='maxclust')
            result = pd.DataFrame(list(zip(ids, durations, cluster_labels)), columns=['sid', 'summeddur', 'label'] )

            # order the sequences based on the order of the leaves in the dendogram
            result = result.reindex(dn['leaves'])
            result = result.reset_index(drop=True)
            result['order'] = result.index

            # sort clusters on average summedduration within cluster
            av_dur = result.groupby(by=['label']).summeddur.mean().sort_values(ascending=False)
            order = av_dur.index.tolist()
            label_dict = {}
            for i in range(len(order)):
                label_dict[order[i]] = i
            result = result.replace({"label" : label_dict})
            result = result.sort_values(['label']).reset_index(drop=True)
            result['order'] = result.index

            ordered = result
            new = pd.merge(intervaldata, ordered, on=['sid'])
            ordereddata = pd.concat([ordereddata, new])
        else:
            new = intervaldata.reset_index(drop=True)
            new['order'] = new.index
            new['label'] = [1] * len(new)
            ordereddata = pd.concat([ordereddata, new])
        
    return ordereddata

# create dataframe for radial view
@lru_cache
def get_radial_df(set, selected_intervals):
    interval_df = get_cached_binned(set, selected_intervals)
    radial_df = radial_cluster(interval_df)

    if len(radial_df) > 0:
        radial_df['start_time'] = radial_df['start_time'].dt.strftime('%Y/%m/%d %H:%M:%S').astype(str)
        radial_df['end_time'] = radial_df['end_time'].dt.strftime('%Y/%m/%d %H:%M:%S').astype(str)
    return radial_df

# function to query a pattern (eventlist + relations) from the selected data (data)
def query(data, eventlist, relations):
    maxg = 10
    highlight = []
    total = data['sid'].nunique()
    ratio = 0
    for sid in data['sid'].unique():
        id_df = data.loc[data['sid'] == sid]
        element_ids = {}
        for k in range(len(eventlist)):
            element_ids[k] = []
        sorted = id_df.sort_values(by='start_time').reset_index(drop=True)
        sorted['start_time'] = pd.to_datetime(sorted['start_time'], errors='coerce')
        total_relations = relations
        break_out_flag = False
        for event_int in range(len(eventlist)):
            nr_relations = len(eventlist[event_int + 1:])
            first_element = eventlist[event_int]
            for rel_int in range(nr_relations):
                second_element = eventlist[event_int + rel_int + 1]
                first_ids = []
                second_ids = []

                if total_relations[rel_int] == 'b':
                    i = 0
                    while i <= len(sorted) - 2:
                        if sorted.iloc[i]['value'] == first_element:
                            end_time = sorted.iloc[i]['end_time']
                            second_id = sorted.loc[(sorted['value'] == second_element) & (sorted['start_time'] > end_time) & ((0 < (sorted['start_time'] - end_time).dt.total_seconds()) & ( (sorted['start_time'] - end_time).dt.total_seconds()  < maxg))]['eid'].tolist()  
                            if len(second_id) > 0:
                                first_id = sorted.iloc[i]['eid']
                                first_ids.append(first_id)
                                second_ids.append(second_id)
                        i += 1

                elif total_relations[rel_int] == 'm':
                        first = sorted.loc[sorted['value'] == first_element]['end_time'].dt.strftime('%Y/%m/%d %H:%M')
                        second = sorted.loc[sorted['value'] == second_element]['start_time'].dt.strftime('%Y/%m/%d %H:%M')
                        times = set(first).intersection(second)
                        first_ids = sorted.loc[(sorted['value'] == first_element) & sorted['end_time'].dt.strftime('%Y/%m/%d %H:%M').isin(times)]['eid'].tolist()
                        second_ids = sorted.loc[(sorted['value'] == second_element) & sorted['start_time'].dt.strftime('%Y/%m/%d %H:%M').isin(times)]['eid'].tolist()
                
                elif total_relations[rel_int] == 'c':
                    i = 0
                    while i <= len(sorted) - 2:
                        if sorted.iloc[i]['value'] == first_element:
                            start_time = sorted.iloc[i]['start_time']
                            end_time = sorted.iloc[i]['end_time']
                            second_id = sorted.loc[(sorted['value'] == second_element) & (sorted['start_time'] > start_time) & (sorted['start_time'] < end_time) & (sorted['end_time'] < end_time)]['eid'].tolist()
                            if len(second_id) > 0:
                                first_id = sorted.iloc[i]['eid']
                                first_ids.append(first_id)
                                second_ids.append(second_id)
                        i += 1

                elif total_relations[rel_int] == 'o':
                    i = 0
                    while i <= len(sorted) - 2:
                        if sorted.iloc[i]['value'] == first_element:
                            start_time = sorted.iloc[i]['start_time']
                            end_time = sorted.iloc[i]['end_time']
                            second_id = sorted.loc[(sorted['value'] == second_element) & (sorted['start_time'] > start_time) & (sorted['start_time'] < end_time) & (sorted['end_time'] > end_time)]['eid'].tolist()
                            if len(second_id) > 0:
                                first_id = sorted.iloc[i]['eid']
                                first_ids.append(first_id)
                                second_ids.append(second_id)
                        i += 1

                elif total_relations[rel_int] == 'f':
                    i = 0
                    while i <= len(sorted) - 2:
                        if sorted.iloc[i]['value'] == first_element:
                            start_time = sorted.iloc[i]['start_time']
                            end_time = sorted.iloc[i]['end_time']
                            second_id = sorted.loc[(sorted['value'] == second_element) & (sorted['start_time'] > start_time) & (sorted['start_time'] < end_time) & (sorted['end_time'].dt.strftime('%Y/%m/%d %H:%M') == end_time.strftime('%Y/%m/%d %H:%M'))]['eid'].tolist()
                            if len(second_id) > 0:
                                first_id = sorted.iloc[i]['eid']
                                first_ids.append(first_id)
                                second_ids.append(second_id)
                        i += 1


                elif total_relations[rel_int] == 'e':
                    first = sorted.loc[sorted['value'] == first_element]
                    first['index'] = first.index
                    second = sorted.loc[sorted['value'] == second_element]
                    second['index'] = second.index
                    result = pd.merge(first, second, how='inner', on=['start_time', 'end_time'] )
                    if len(result) > 0:
                        ind_list = result[['index_x', 'index_y']].values.tolist()
                        indices = [item for sublist in ind_list for item in sublist]
                        index = sorted.iloc[indices]
                        first_ids = index.loc[index['value'] == first_element]['eid'].values.tolist()
                        second_ids = index.loc[index['value'] == second_element]['eid'].values.tolist()
                        

                elif total_relations[rel_int] == 's':
                    i = 0
                    while i <= len(sorted) - 2:
                        if sorted.iloc[i]['value'] == first_element:
                            start_time = sorted.iloc[i]['start_time']
                            end_time = sorted.iloc[i]['end_time']
                            second_id = sorted.loc[(sorted['value'] == second_element) & (sorted['start_time'].dt.strftime('%Y/%m/%d %H:%M') == start_time.strftime('%Y/%m/%d %H:%M')) & (sorted['end_time'] > end_time)]['eid'].tolist()
                            if len(second_id) > 0:
                                first_id = sorted.iloc[i]['eid']
                                first_ids.append(first_id)
                                second_ids.append(second_id)
                        i += 1
                
                # flatten list if necessary
                if any(isinstance(i, list) for i in first_ids):
                    first_ids = [item for sublist in first_ids for item in sublist]
                if any(isinstance(i, list) for i in second_ids):
                    second_ids = [item for sublist in second_ids for item in sublist]

                if (len(first_ids) == 0) | (len(second_ids) == 0):
                    break_out_flag = True
                    break
                if len(element_ids[event_int])!= 0:
                    first_ids = list(set(first_ids).intersection(element_ids[event_int]))
                if len(element_ids[event_int + rel_int + 1])!= 0:
                    second_ids = list(set(second_ids).intersection(element_ids[event_int + rel_int + 1]))

                element_ids[event_int] = first_ids
                element_ids[event_int + rel_int + 1] = second_ids  
            total_relations = total_relations[nr_relations:]

            if break_out_flag:
                break

        highlight_ids = list(element_ids.values())
        if any(isinstance(i, list) for i in highlight_ids):
            highlight_ids = [item for sublist in highlight_ids for item in sublist]
        # update ratio to compute support 
        if len(highlight_ids) > 0:
            ratio +=1
        highlight.append(highlight_ids)
    if any(isinstance(i, list) for i in highlight):
        highlight = [item for sublist in highlight for item in sublist]
    highlight = [int(item) for item in highlight]
    support = ratio / total
    return highlight, support

# get cached data, bin by day, filter if necessary
@lru_cache
def get_cached_binned(set, filter=False):
    fulldf = get_intervaldata(set)
    if filter:
        fulldf = filter_intervaldata(fulldf, filter)
    binned_df = bin_intervals_byday(fulldf)
    return binned_df




#########################################################
# Flask routes
#######################################################

@app.route("/")
def client():
    return send_from_directory('client/public', 'index.html')


# return groupdictionary for data selection
@app.route("/get_groups", methods=['GET'])
def get_groups():
    f = open(data_directory + "/groupdict.json")
    groupdict = json.load(f)
    users_w_data = os.listdir(data_directory)
    for key in groupdict.keys():
        update = list(set(groupdict[key]).intersection(users_w_data))
        groupdict[key] = update
    print("groupdict:", groupdict)
    return jsonify(groupdict)


# return events and corresponding atttributes
@app.route("/get_events_attributes", methods=['GET'])
def json_events():
    attributes = []
    for event in events:
        attributes.append(get_attributes(event))
    return jsonify([events, attributes])

# return mean duration and frequency for each interval by day (sid), will be used to show attribute matrices
@app.route("/get_attr_matrices/<set>", methods=['GET'])
def get_attr_matrices(set):
    binned_df = get_cached_binned(set)

    # compute df with total daily duration and frequency for each interval
    summeddur = binned_df.groupby(by=['sid', 'value']).duration.sum().reset_index()
    frequency = binned_df.groupby(by=['sid', 'value']).size().reset_index()
    frequency.rename(columns= {0: 'frequency'}, inplace=True)
    total = pd.merge(summeddur, frequency, on=['sid', 'value'])

    # compute df with mean daily duration and frequency for each interval
    mean_summeddur = total.groupby(by=['value']).duration.mean().reset_index()
    mean_frequency = total.groupby(by=['value']).frequency.mean().reset_index()
    summary = pd.merge(mean_summeddur, mean_frequency, on=['value'])

    summary[['event', 'attr1', 'attr2']] = summary['value'].str.split("/", expand=True)

    summary = summary.to_json(orient="records")
    summary = json.loads(summary)
    return jsonify(summary)


# return summary dataframe that includes mean duration and frequency for selected intervals of selected duration within timeframe
@app.route("/get_summary_data/<set>/<selected_intervals>/<selected_durs>/<selectedhours>", methods=["GET"])
def get_summary_data(set, selected_intervals, selected_durs, selectedhours):
    print("loading summary data")
    if selectedhours == "undefined":
        binned_df = get_cached_binned(set, selected_intervals)
        selecteddurs = json.loads(selected_durs)
         # filter the dataframe on selected durations, if no duration is selected for a selected interval, include all durations
        for key in selecteddurs:
            interval = key.replace("-", "/")
            durations = selecteddurs[key]
            intervaldf = binned_df.loc[binned_df['value'] == interval]
            intervaldf = intervaldf.loc[(float(durations[0]) <= intervaldf['duration'].astype(float)) & (intervaldf['duration'].astype(float) <= float(durations[1]))]
            binned_df = binned_df.loc[binned_df['value'] != interval]
            binned_df = pd.concat([binned_df, intervaldf])
        binned_df['duration'] = (binned_df['end_time'] - binned_df['start_time']).astype('timedelta64[m]')
    else:
        binned_df = bin_intervals_custom(set, selected_intervals, selected_durs, selectedhours)

    # compute df with total daily duration and frequency for each selected interval
    summeddur = binned_df.groupby(by=['sid', 'value']).duration.sum().reset_index()
    frequency = binned_df.groupby(by=['sid', 'value']).size().reset_index()
    frequency.rename(columns= {0: 'frequency'}, inplace=True)
    total = pd.merge(summeddur, frequency, on=['sid', 'value'])

    # compute df with mean daily duration and frequency for each interval
    mean_summeddur = total.groupby(by=['value']).duration.mean().reset_index()
    mean_frequency = total.groupby(by=['value']).frequency.mean().reset_index()
    summary = pd.merge(mean_summeddur, mean_frequency, on=['value'])

    summary = summary.to_json(orient="records")
    summary = json.loads(summary)
    return jsonify(summary)

# return mined patterns based on selected intervals, and optional: durations, timeframe and one specific interval of interest
@app.route("/get_pattern_data/<set>/<selected_intervals>/<selected_durs>/<selectedhours>/<filterby>", methods=["GET"])
def get_pattern_data(set, selected_intervals, selected_durs, selectedhours, filterby):
    filterby = json.loads(filterby).replace("-", "/") 
    print("mine patterns")
    # add sequence ids based on selected timeframe
    if selectedhours == "undefined":
        binned_df = get_cached_binned(set, selected_intervals)
        selecteddurs = json.loads(selected_durs)
         # filter the dataframe on selected durations, if no duration is selected for a selected interval, include all durations
        for key in selecteddurs:
            interval = key.replace("-", "/")
            durations = selecteddurs[key]
            intervaldf = binned_df.loc[binned_df['value'] == interval]
            intervaldf = intervaldf.loc[(float(durations[0]) <= intervaldf['duration'].astype(float)) & (intervaldf['duration'].astype(float) <= float(durations[1]))]
            binned_df = binned_df.loc[binned_df['value'] != interval]
            binned_df = pd.concat([binned_df, intervaldf])
        binned_df['duration'] = (binned_df['end_time'] - binned_df['start_time']).astype('timedelta64[m]')
    else:
        binned_df = bin_intervals_custom(set, selected_intervals, selected_durs, selectedhours)

    if len(binned_df) > 1:
        # filter df by interval of interest (optional)
        if filterby != 'all':
            for sequence in binned_df['sid'].unique():
                seqdf = binned_df.loc[binned_df['sid'] == sequence]
                if filterby not in seqdf['value'].unique():
                    binned_df = binned_df.loc[binned_df['sid'] != sequence]

        # mine patterns from sequences
        ruledf = mine_seqs(binned_df)
        # format resulting pattern csv file into pandas dataframe
        ruledf = format_patterns()

        # query the patterns to find the accurate support
        print("ruledf", ruledf)
        finalrules = pd.DataFrame()
        for pattern_id in ruledf['pattern_id'].unique():
            print("pattern_id", pattern_id)
            pattern_df = ruledf.loc[ruledf['pattern_id'] == pattern_id]
            if ('c' in pattern_df.iloc[0]['relations']) or ('s' in pattern_df.iloc[0]['relations']):
                print(pattern_df.iloc[0]['relations'])
                highlight, support = query(binned_df, pattern_df['interval'].tolist(), pattern_df.iloc[0]['relations'])
                print("support", highlight, support)
            # pattern_df['highlight'] = [highlight] * len(pattern_df)
                pattern_df['support'] = [support] * len(pattern_df)
            finalrules = pd.concat([finalrules, pattern_df])
        print("finalrules", finalrules)

        # retrieve the five patterns with highest vertical support
        if len(finalrules) > 0: 
            finalrules['support'] = finalrules['support'].astype(float)
            supp = finalrules.groupby(by=['pattern_id'])['support'].first().sort_values(ascending=False)
            order = supp.index.tolist()
            label_dict = {}
            for i in range(len(order)):
                label_dict[order[i]] = i
            finalrules = finalrules.replace({"pattern_id" : label_dict})
            finalrules = finalrules.sort_values(['pattern_id']).reset_index(drop=True)
            finalrules = finalrules.loc[finalrules['pattern_id'] <= 10]
    else:
        finalrules = pd.DataFrame()
    print("finalrules", finalrules)
    finalrules = finalrules.to_json(orient='records')
    finalrules = json.loads(finalrules)
    return jsonify(finalrules)


# return the dataframe for radial clustering, which includes the selected intervals and the cluster label
@app.route("/get_intervals/<set>/<selected_intervals>", methods=["GET"])
def get_intervals(set, selected_intervals):
    radial_df = get_radial_df(set, selected_intervals)
    radial_df = radial_df.to_json(orient='records')
    radial_df = json.loads(radial_df)
    radial_df = jsonify(radial_df)
    return radial_df

# return the ids from events that adhere to the selected pattern (eventlist + relation), by querying the pattern
@app.route("/highlight_patterns/<set>/<selected_intervals>/<selected_durs>/<selectedhours>/<eventlist>/<relations>", methods=["GET"])
def highlight_patterns(set, selected_intervals, selected_durs, selectedhours, eventlist, relations):
    if selectedhours == "undefined":
        binned_df = get_cached_binned(set, selected_intervals)
        selecteddurs = json.loads(selected_durs)
         # filter the dataframe on selected durations, if no duration is selected for a selected interval, include all durations
        for key in selecteddurs:
            interval = key.replace("-", "/")
            durations = selecteddurs[key]
            intervaldf = binned_df.loc[binned_df['value'] == interval]
            intervaldf = intervaldf.loc[(float(durations[0]) <= intervaldf['duration'].astype(float)) & (intervaldf['duration'].astype(float) <= float(durations[1]))]
            binned_df = binned_df.loc[binned_df['value'] != interval]
            binned_df = pd.concat([binned_df, intervaldf])
    else:
        binned_df = bin_intervals_custom(set, selected_intervals, selected_durs, selectedhours)
    eventlist = json.loads(eventlist)
    new_eventlist = []
    for event in eventlist:
        new_eventlist.append(event.replace("-", "/") )
    highlight_ids, support = query(binned_df, new_eventlist, relations)
    print("select", new_eventlist, relations)
    highlight_ids = jsonify(highlight_ids)
    return highlight_ids



if __name__ == "__main__":
    app.run(debug=True)
