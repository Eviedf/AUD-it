import random
import pandas as pd
from tqdm import tqdm
import numpy as np
import ast
import json
import pickle
import os

pd.set_option('mode.chained_assignment', None)

def get_events():
    events = [
        'connectivity',
        'light_lux',
        # 'notification',
        'powerState',
        'usage',
        'sms',
        'activity',
        'call',
        'bluetooth',
        'acceleration'
    ]
    return events



def get_value(events):
    values = []
    for event in events:
        if event == 'connectivity':
            values.append(random.choice(['wifi', 'offline', 'cellular']))
        elif (event == 'light_lux' or event == 'acceleration'):
            values.append(random.choice(['low', 'medium', 'high']))
        elif (event == 'notification'):
            values.append(random.choice(
                ['post', 'remove', 'post_facebook', 'remove_facebook', 'post_instagram',
                 'remove_instagram', 'post_snapchat', 'remove_snapchat', 'post_whatsapp',
                 'remove_whatsapp']))
        elif (event == 'powerState'):
            values.append(random.choice(
                ['screen_on', 'screen_off', 'power_connected', 'shutdown', 'boot_completed',
                 'airplane_mode_changed']))
        elif (event == 'usage'):
            values.append(random.choice(
                ['to_foreground', 'start_screen_non_interactive', 'start_keyguard_shown',
                 'start_screen_interactive', 'start_keyguard_hidden',
                 'start_foreground_service', 'stop_foreground_service']))
        elif (event == 'sms'):
            values.append(random.choice(['inbox', 'sent']))
        elif (event == 'activity'):
            values.append(random.choice(
                ['inVehicle', 'onBycicle', 'onFoot', 'running', 'still', 'tilting', 'unknown']))
        elif (event == 'call'):
            values.append(random.choice(
                ['outgoing_start', 'outgoing_end', 'incoming_start', 'incoming_end', 'missed',
                 'outgoing', 'rejected', 'blocked']))
        else:
            values.append(random.randint(0, 3))
    return values

def get_event_intervals(id, timedata, event):
    id_df = pd.DataFrame(columns=['sid', 'start_time', 'end_time', 'value'])
    filtered = timedata[timedata['event'] == event]
    if len(filtered) > 1:
        filtered["measuredAt"] = pd.to_datetime(
            filtered["measuredAt"], utc=False)
        filtered = filtered.sort_values(by='measuredAt', ascending=True)
        filtered['measuredAt'] = filtered['measuredAt'].dt.strftime("%Y/%m/%d %H:%M")
        filtered = filtered.reset_index(drop=True)
        for i, row in filtered.iterrows():
            j = i + 1
            while j < len(filtered):
                if filtered.iloc[j]['measuredAt'] == row['measuredAt']:
                    j += 1
                else:
                    id_df.loc[len(id_df)] = [id, row['measuredAt'], filtered.iloc[j]['measuredAt'], event + "/" + str(row['value']) + "/" + str(filtered.iloc[j]['value'])]
                    break 
                k = j + 1
                while k < len(filtered):
                    if filtered.iloc[j]['measuredAt'] == filtered.iloc[k]['measuredAt']:
                        id_df.loc[len(id_df)] = [id, row['measuredAt'], filtered.iloc[k]['measuredAt'],  event + "/" + str(row['value']) + "/" + str(filtered.iloc[j]['value'])]
                        k += 1
                    else:
                        break
    return id_df

def create_timedata():
    ids = 60
    values = 500
    for i in tqdm(range(ids)):
        id = [i] * values
        timestamp = [
            f'2022/01/{random.randint(20,23)} {random.randint(0,23)}:{random.randint(0,59)}:{random.randint(0,59)}' for x in range(values)]
        event = random.choices(['connectivity', 'light_lux', 'notification', 'usage',
                            'sms', 'activity', 'acceleration', 'bluetooth', 'call', 'powerState'], k=values)
        value = get_value(event)
        df = pd.DataFrame(list(zip(id, timestamp, event, value)), columns=[
                        'participantId', 'measuredAt', 'event', 'value'])
        path = 'datasets/%s' % str(i)
        isExists = os.path.exists(path)
        if not isExists:
            os.makedirs(path)
        df.to_pickle("./datasets/" + str(i) + "/timedata.pickle")
        del df

def create_intervaldata():
    events = get_events()
    for id in os.listdir("./datasets"):
        print("id", id)
        timedata = pd.read_pickle("./datasets/%s" % id + "/timedata.pickle")
        intervaldata = pd.DataFrame(
            columns=['sid', 'start_time', 'end_time', 'value'])
        for event in events:
            eventdf = get_event_intervals(id, timedata, event)
            if len(eventdf) > 0:
                intervaldata = pd.concat([intervaldata, eventdf])
        intervaldata.to_pickle("./datasets/" + id + "/intervaldata.pickle")

def create_groupdict():
    groupdict = {
        "group_0":  [str(x) for x in list(range(0, 11))],
        "group_1": [str(x) for x in list(range(11, 22))],
        "group_2": [str(x) for x in list(range(22, 50))],
        "group_3": [str(x) for x in list(range(50, 60))]
    }
    with open('./datasets/groupdict.json', 'w') as fp:
        json.dump(groupdict, fp)

create_timedata()
create_intervaldata()
create_groupdict()
