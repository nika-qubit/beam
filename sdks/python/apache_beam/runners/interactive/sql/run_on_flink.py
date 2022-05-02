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

"""Module to support running beam_sql_magics on Flink."""

import logging

import apache_beam as beam
from apache_beam.runners.interactive.sql.utils import OptionsEntry
from apache_beam.runners.interactive.sql.utils import OptionsForm

_LOGGER = logging.getLogger(__name__)


class FlinkOptionsForm(OptionsForm):
  def __init__(
      self,
      output_name: str,
      output_pcoll: beam.PCollection,
      verbose: bool = False):
    super().__init__()
    self.p = output_pcoll.pipeline
    self.output_name = output_name
    self.output_pcoll = output_pcoll
    self.verbose = verbose
    self.notice_shown = False
    self.add()
