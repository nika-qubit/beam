#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import logging
from datetime import timedelta

from apache_beam.runners.interactive import interactive_environment as ie
from apache_beam.runners.interactive.interactive_beam import *

try:
  from timeloop import Timeloop
  import apache_beam as beam
  import ipywidgets as widgets
  from IPython.display import display
  from sidecar import Sidecar

  _inspect_ready = True
except ImportError:
  _inspect_ready = False


class InteractiveEnvironmentInspector(object):

  def __init__(self):
    self._pipelines = {}
    self._pcolls = {}
    self._all = {}
    if _inspect_ready:
      self.refresh()
      Sidecar.close_all()
      self._panel = Sidecar(title='Interactive Beam Inspector')
      self._handle = None

  def refresh(self):
    self._pipelines, self._pcolls = inspect_defined_pipelines_and_pcolls()
    self._all = {}
    self._all.update(self._pipelines)
    self._all.update(self._pcolls)

  def get_val(self, idlized_name):
    return self._all.get(idlized_name, None)

  def display(self):
    # If deps are not ready or a display is started, NOOP.
    if not _inspect_ready:
      return

    w_select = widgets.Select(
        options=list(self._all.keys()),
        value=None
    )
    up = widgets.HBox([w_select])
    w_output = widgets.Output()
    down = widgets.HBox([w_output])

    def on_select(change):
      idlized_name = change['new']
      val = self.get_val(idlized_name)
      with w_output:
        w_output.clear_output()
        if isinstance(val, beam.pipeline.Pipeline):
          show_graph(val)
        elif isinstance(val, beam.pvalue.PCollection):
          show(val)

    w_select.observe(on_select, names='value')
    with self._panel:
      display(widgets.VBox([up, down],
                           layout=widgets.Layout(
                               display='flex',
                               width='100%',
                               height='100%',
                               overflow='scroll')))
    # Disable the verbose logging from timeloop.
    logging.getLogger('timeloop').disabled = True
    self._handle = Timeloop()

    def continuous_display_inspector(inspector, w_select, tl):

      @tl.job(interval=timedelta(seconds=1.5))
      def update():
        inspector.refresh()
        new_options = list(self._all.keys())
        if set(new_options) != set(w_select.options):
          w_select.options = new_options

      tl.start()

    continuous_display_inspector(self, w_select, self._handle)

  def close(self):
    if self._handle:
      self._handle.stop()
    if self._panel:
      self._panel.close_all()


# Adaptors.

def inspect_defined_pipelines_and_pcolls():
  pipelines = {}
  pcolls = {}
  for watching in ie.current_env().watching():
    for name, val in watching:
      if isinstance(val, beam.pipeline.Pipeline):
        pipelines[idlize(name, val)] = val
      elif isinstance(val, beam.pvalue.PCollection):
        pcolls[idlize(name, val)] = val
  return pipelines, pcolls


def idlize(name, val):
  return '{} (id: {}, type: {})'.format(name, id(val), type(val).__name__)
