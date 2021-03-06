# Copyright 2014 Tennessee Leeuwenburg

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
from time import gmtime
from time import strftime

from . import analysers
from . import points

def generic():

    return AutoGraph()

class Graph():

    def as_dict(self):
        raise NotImplementedError


class AutoGraph(Graph):

    def auto_ingest(self, raw_data):

        self.raw_data = raw_data

        return

class GraphiteGraph(Graph):

    """Graphite is timeseries, so we know that the x-axis will always be time."""

    def __init__(self):

        self.defaults = {
            'title': None,
            'x_axis': {
                'label': 'time',
                'min': sys.maxsize,
                'max': -1 * sys.maxsize
            },
            'y_axis': {
                'label': 'metric',
                'min': sys.maxsize,
                'max': -1 * sys.maxsize
            },
            "series": []

        }

    def auto_ingest(self, raw_data):
        '''
        Stores the raw data into self.raw_data
        Stores structured data into self.processed_data
        Creates the response for as_dist ad self.result
        '''

        self.raw_data = raw_data
        self.result_dict = self.defaults.copy()

        for series in self.raw_data['graphite_data']:
            self._create_series(series)

        if 'title' in raw_data:
            self.result_dict['title'] = raw_data['title']

    def as_dict(self):

        readable_dict = self.result_dict.copy()
        readable_dict['x_axis']['max'] = self._to_readable_date(readable_dict['x_axis']['max'])
        readable_dict['x_axis']['min'] = self._to_readable_date(readable_dict['x_axis']['min'])
        for item in readable_dict['series']:
            item['start_value']['x'] = self._to_readable_date(item['start_value']['x'])
            item['end_value']['x'] = self._to_readable_date(item['end_value']['x'])
        return readable_dict

    def _to_readable_date(self, datestring):
        readable_date = gmtime(int(datestring))
        return strftime("%d %b %Y %H:%M:%S", readable_date)

    def _create_series(self, series):

        values = self._convert_points(series['datapoints'])
        self._update_extremes(values)
        analysis = analysers.get_analysis(values)

        series_dict = {
            "name": series['target'],
            "distribution": analysis['name'],
            "min_y_value": analysis['min_y_value'],
            "fit": analysis['p_value'],
            "start_value": {"x": values[0].x, "y": values[0].y},
            "end_value": {"x": values[-1].x, "y": values[-1].y}
        }

        self.result_dict['series'].append(series_dict)

    def _update_extremes(self, values):

        min_x = self.result_dict['x_axis']['min']
        max_x = self.result_dict['x_axis']['max']
        min_y = self.result_dict['y_axis']['min']
        max_y = self.result_dict['y_axis']['max']
        for x, y in values:
            min_x = min(x, min_x)
            min_y = min(y, min_y)
            max_x = max(x, max_x)
            max_y = max(y, max_y)
        self.result_dict['x_axis']['min'] = min_x
        self.result_dict['x_axis']['max'] = max_x
        self.result_dict['y_axis']['min'] = min_y
        self.result_dict['y_axis']['max'] = max_y

    def _convert_points(self, list_of_points):
        # NOTE: Graphite uses None for "no value", but want to plot at '0'
        the_points = [points.Point(x, y or 0) for [y, x] in list_of_points]
        return the_points
