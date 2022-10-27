# AUD-it
AUD-it is an interactive web-application that supports the exploration of interval-based events in (1) a temporal context and (2) in context to other events. In order to run AUD-it with a dataset of interest, one can follow the following steps.
An instruction video can be found on: https://youtu.be/agVUjR1xvfQ

## 1. Format the data
Since AUD-it supports the exploration of intervals between events and relations between these intervals, the data needs to be formatted to contain the possible intervals in the data. As input data, the data should be structured according to the figure below:
![dataformat](https://user-images.githubusercontent.com/25794934/197168477-54e5f57d-4ac8-4ff6-ac11-9ed41fe62964.png)

Each row consists of an interval, where _sid_ is the identifier of the source, in this case a person. _start_time_ and _end_time_ indicate the starting and ending time of the interval. Value indicates the interval itself which includes the event type, the first value of the interval and the second value of the interval. To give an example, ‘_powerState/screen off/screen on_’ indicates a powerState interval from screen off to screen on. A dictionary called _groupdict.json_ should be included that assigns the different data directories to different groups.

In _backend/server.py_, the data directory can be renamed, by default it is set to: _"data/datasets"_. We included a _dummydata/dummydata.py_, this code can be run to create dummy data, in _'dummydata/datasets'_ , note that the resulting data is random and will not reveal interesting patterns or use cases in AUD-it. 

## 2. Install requirements 
1. Install the backend requirements for this project by calling pip install ```-r /path/to/requirements.txt```
2. Install pnpm (see https://pnpm.io/installation)
3. Install the frontend requirements for this project by calling ```pnpm install``` within the frontend directory

## 3. Run the application
1. Run the backend by running _backend/server.py_
2. Run the frontend by calling ``` pnpm dev ``` within the frontend directory
3. Go to _http://localhost:3000/_ in your browser, you can now use AUD-it to explore your data!
![finaldesign](https://user-images.githubusercontent.com/25794934/197172162-44cc3ad7-9b9f-4cc9-b4c1-1de292170b06.png)
