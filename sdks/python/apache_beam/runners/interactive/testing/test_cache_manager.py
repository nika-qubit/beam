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
from __future__ import absolute_import


import collections
import itertools

import apache_beam as beam
from apache_beam import coders
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileHeader
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileRecord
from apache_beam.portability.api.beam_runner_api_pb2 import TestStreamPayload
from apache_beam.runners.interactive.cache_manager import CacheManager
from apache_beam.utils.timestamp import Timestamp


class InMemoryCache(CacheManager):
  def __init__(self):
    self._cached = collections.defaultdict(list)
    self._pcoders = {}

  def exists(self, *labels):
    return self._key(*labels) in self._cached

  def _latest_version(self, *labels):
    return True

  def read(self, *labels):
    ret = itertools.chain(self._cached[self._key(*labels)])
    return ret, None

  def write(self, value, *labels):
    self._cached[self._key(*labels)] += value

  def save_pcoder(self, pcoder, *labels):
    self._pcoders[self._key(*labels)] = pcoder

  def load_pcoder(self, *labels):
    return self._pcoders[self._key(*labels)]

  def _key(self, *labels):
    return ''.join([l for l in labels])

  def cleanup(self):
    self._cached = collections.defaultdict(list)
    self._pcoders = {}

  def sink(self, *labels):
    return NoopSink()


class NoopSink(beam.PTransform):
  def expand(self, pcoll):
    return pcoll | beam.Map(lambda x: x)


class FileRecordsBuilder(object):
  def __init__(self, tag=None):
    self._header = TestStreamFileHeader(tag=tag)
    self._records = []
    self._coder = coders.FastPrimitivesCoder()

  def add_element(self, element, event_time, processing_time):
    element_payload = TestStreamPayload.Event.AddElements(
        elements=[TestStreamPayload.TimestampedElement(
            encoded_element=self._coder.encode(element),
            timestamp=Timestamp.of(event_time).micros)])
    record = TestStreamFileRecord(
        element_event=element_payload,
        processing_time=Timestamp.of(processing_time).to_proto())
    self._records.append(record)
    return self

  def advance_watermark(self, watermark, processing_time):
    record = TestStreamFileRecord(
        watermark_event=TestStreamPayload.Event.AdvanceWatermark(
            new_watermark=Timestamp.of(watermark).micros),
        processing_time=Timestamp.of(processing_time).to_proto())
    self._records.append(record)
    return self

  def build(self):
    return [self._header] + self._records
