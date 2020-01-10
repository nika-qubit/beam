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

"""Provides TestStream for verifying streaming runner semantics.

For internal use only; no backwards-compatibility guarantees.
"""
# pytype: skip-file

from __future__ import absolute_import

from abc import ABCMeta
from abc import abstractmethod
from builtins import object
from functools import total_ordering

from future.utils import with_metaclass

import apache_beam as beam
from apache_beam import coders
from apache_beam import pvalue
from apache_beam.portability import common_urns
from apache_beam.portability.api import beam_runner_api_pb2
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileHeader
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileRecord
from apache_beam.portability.api.beam_runner_api_pb2 import TestStreamPayload
from apache_beam.transforms import PTransform
from apache_beam.transforms import core
from apache_beam.transforms import window
from apache_beam.transforms.timeutil import TimeDomain
from apache_beam.transforms.userstate import on_timer
from apache_beam.transforms.userstate import TimerSpec
from apache_beam.transforms.window import TimestampedValue
from apache_beam.utils.timestamp import MIN_TIMESTAMP
from apache_beam.utils.timestamp import Duration
from apache_beam.utils import timestamp
from apache_beam.utils.windowed_value import WindowedValue

__all__ = [
    'Event',
    'ElementEvent',
    'WatermarkEvent',
    'ProcessingTimeEvent',
    'TestStream',
]


@total_ordering
class Event(with_metaclass(ABCMeta, object)):  # type: ignore[misc]
  """Test stream event to be emitted during execution of a TestStream."""
  @abstractmethod
  def __eq__(self, other):
    raise NotImplementedError

  @abstractmethod
  def __hash__(self):
    raise NotImplementedError

  @abstractmethod
  def __lt__(self, other):
    raise NotImplementedError

  def __ne__(self, other):
    # TODO(BEAM-5949): Needed for Python 2 compatibility.
    return not self == other

  @abstractmethod
  def to_runner_api(self, element_coder):
    raise NotImplementedError

  @staticmethod
  def from_runner_api(proto, element_coder):
    if proto.HasField('element_event'):
      return ElementEvent([
          TimestampedValue(
              element_coder.decode(tv.encoded_element),
              timestamp.Timestamp(micros=1000 * tv.timestamp))
          for tv in proto.element_event.elements
      ])
    elif proto.HasField('watermark_event'):
      return WatermarkEvent(
          timestamp.Timestamp(
              micros=1000 * proto.watermark_event.new_watermark))
    elif proto.HasField('processing_time_event'):
      return ProcessingTimeEvent(
          timestamp.Duration(
              micros=1000 * proto.processing_time_event.advance_duration))
    else:
      raise ValueError(
          'Unknown TestStream Event type: %s' % proto.WhichOneof('event'))


class ElementEvent(Event):
  """Element-producing test stream event."""
  def __init__(self, timestamped_values, tag=None):
    self.timestamped_values = timestamped_values
    self.tag = tag

  def __eq__(self, other):
    if not isinstance(other, ElementEvent):
      raise TypeError

    return (self.timestamped_values == other.timestamped_values and
            self.tag == other.tag)

  def __hash__(self):
    return hash(self.timestamped_values)

  def __lt__(self, other):
    if not isinstance(other, ElementEvent):
      raise TypeError

    return self.timestamped_values < other.timestamped_values

  def to_runner_api(self, element_coder):
    return beam_runner_api_pb2.TestStreamPayload.Event(
        element_event=beam_runner_api_pb2.TestStreamPayload.Event.AddElements(
            elements=[
                beam_runner_api_pb2.TestStreamPayload.TimestampedElement(
                    encoded_element=element_coder.encode(tv.value),
                    timestamp=tv.timestamp.micros // 1000)
                for tv in self.timestamped_values
            ]))

  def __repr__(self):
    return 'ElementEvent: <{}, {}>'.format(
        [(e.value, e.timestamp) for e in self.timestamped_values], self.tag)


class WatermarkEvent(Event):
  """Watermark-advancing test stream event."""
  def __init__(self, new_watermark, tag=None):
    self.new_watermark = timestamp.Timestamp.of(new_watermark)
    self.tag = tag

  def __eq__(self, other):
    if not isinstance(other, WatermarkEvent):
      raise TypeError

    return self.new_watermark == other.new_watermark and self.tag == other.tag

  def __hash__(self):
    return hash(self.new_watermark)

  def __lt__(self, other):
    if not isinstance(other, WatermarkEvent):
      raise TypeError

    return self.new_watermark < other.new_watermark

  def to_runner_api(self, unused_element_coder):
    return beam_runner_api_pb2.TestStreamPayload.Event(
        watermark_event=beam_runner_api_pb2.TestStreamPayload.Event.
        AdvanceWatermark(new_watermark=self.new_watermark.micros // 1000))


  def __repr__(self):
    return 'WatermarkEvent: <{}, {}>'.format(self.new_watermark, self.tag)

class ProcessingTimeEvent(Event):
  """Processing time-advancing test stream event."""
  def __init__(self, advance_by):
    self.advance_by = Duration.of(advance_by)

  def __eq__(self, other):
    if not isinstance(other, ProcessingTimeEvent):
      raise TypeError

    return self.advance_by == other.advance_by

  def __hash__(self):
    return hash(self.advance_by)

  def __lt__(self, other):
    if not isinstance(other, ProcessingTimeEvent):
      raise TypeError

    return self.advance_by < other.advance_by

  def to_runner_api(self, unused_element_coder):
    return beam_runner_api_pb2.TestStreamPayload.Event(
        processing_time_event=beam_runner_api_pb2.TestStreamPayload.Event.
        AdvanceProcessingTime(advance_duration=self.advance_by.micros // 1000))

  def __repr__(self):
    return 'ProcessingTimeEvent: <{}>'.format(self.advance_by)


class TestStream(PTransform):
  """Test stream that generates events on an unbounded PCollection of elements.

  Each event emits elements, advances the watermark or advances the processing
  time. After all of the specified elements are emitted, ceases to produce
  output.
  """
  def __init__(self, coder=coders.FastPrimitivesCoder(), events=None,
               output_tags=None):
    super(TestStream, self).__init__()
    assert coder is not None
    self.coder = coder
    self.watermarks = {None: timestamp.MIN_TIMESTAMP}
    self._events = list(events) if events is not None else []
    self.output_tags = set(output_tags) if output_tags is not None else set()

  def get_windowing(self, unused_inputs):
    return core.Windowing(window.GlobalWindows())

  def _infer_output_coder(self, input_type=None, input_coder=None):
    return self.coder

  def expand(self, pbegin):
    assert isinstance(pbegin, pvalue.PBegin)
    self.pipeline = pbegin.pipeline
    return pvalue.PCollection(self.pipeline, is_bounded=False)

  def _add(self, event):
    if isinstance(event, ElementEvent):
      for tv in event.timestamped_values:
        assert tv.timestamp < timestamp.MAX_TIMESTAMP, (
            'Element timestamp must be before timestamp.MAX_TIMESTAMP.')
    elif isinstance(event, WatermarkEvent):
      if event.tag not in self.watermarks:
        self.watermarks[event.tag] = timestamp.MIN_TIMESTAMP
      assert event.new_watermark > self.watermarks[event.tag], (
          'Watermark must strictly-monotonically advance.')
      self.watermarks[event.tag] = event.new_watermark
    elif isinstance(event, ProcessingTimeEvent):
      assert event.advance_by > 0, (
          'Must advance processing time by positive amount.')
    else:
      raise ValueError('Unknown event: %s' % event)
    self._events.append(event)

  def add_elements(self, elements, tag=None, event_timestamp=None):
    """Add elements to the TestStream.

    Elements added to the TestStream will be produced during pipeline execution.
    These elements can be TimestampedValue, WindowedValue or raw unwrapped
    elements that are serializable using the TestStream's specified Coder.  When
    a TimestampedValue or a WindowedValue element is used, the timestamp of the
    TimestampedValue or WindowedValue will be the timestamp of the produced
    element; otherwise, the current watermark timestamp will be used for that
    element.  The windows of a given WindowedValue are ignored by the
    TestStream.
    """
    self.output_tags.add(tag)
    timestamped_values = []
    if tag not in self.watermarks:
      self.watermarks[tag] = timestamp.MIN_TIMESTAMP

    for element in elements:
      if isinstance(element, TimestampedValue):
        timestamped_values.append(element)
      elif isinstance(element, WindowedValue):
        # Drop windows for elements in test stream.
        timestamped_values.append(
            TimestampedValue(element.value, element.timestamp))
      else:
        # Add elements with timestamp equal to current watermark.
        if event_timestamp is None:
          event_timestamp = self.watermarks[tag]
        timestamped_values.append(TimestampedValue(element, event_timestamp))
    self._add(ElementEvent(timestamped_values, tag))
    return self

  def advance_watermark_to(self, new_watermark, tag=None):
    """Advance the watermark to a given Unix timestamp.

    The Unix timestamp value used must be later than the previous watermark
    value and should be given as an int, float or utils.timestamp.Timestamp
    object.
    """
    self.output_tags.add(tag)
    self._add(WatermarkEvent(new_watermark, tag))
    return self

  def advance_watermark_to_infinity(self, tag=None):
    """Advance the watermark to the end of time, completing this TestStream."""
    self.advance_watermark_to(timestamp.MAX_TIMESTAMP, tag)
    return self

  def advance_processing_time(self, advance_by):
    """Advance the current processing time by a given duration in seconds.

    The duration must be a positive second duration and should be given as an
    int, float or utils.timestamp.Duration object.
    """
    self._add(ProcessingTimeEvent(advance_by))
    return self

  def to_runner_api_parameter(self, context):
    return (
        common_urns.primitives.TEST_STREAM.urn,
        beam_runner_api_pb2.TestStreamPayload(
            coder_id=context.coders.get_id(self.coder),
            events=[e.to_runner_api(self.coder) for e in self._events]))

  @staticmethod
  @PTransform.register_urn(
      common_urns.primitives.TEST_STREAM.urn,
      beam_runner_api_pb2.TestStreamPayload)
  def from_runner_api_parameter(payload, context):
    coder = context.coders.get_by_id(payload.coder_id)
    return TestStream(
        coder=coder,
        events=[Event.from_runner_api(e, coder) for e in payload.events])


class _TimingInfoReporter(PTransform):
  def expand(self, pcoll):
    return pvalue.PCollection.from_(pcoll)


class _TimingInfo(object):
  def __init__(self, event_timestamp, processing_time, watermark):
    self._event_timestamp = timestamp.Timestamp.of(event_timestamp)
    self._processing_time = timestamp.Timestamp.of(processing_time)
    self._watermark = timestamp.Timestamp.of(watermark)

  @property
  def event_timestamp(self):
    return self._event_timestamp

  @property
  def processing_time(self):
    return self._processing_time

  @property
  def watermark(self):
    return self._watermark

  def __repr__(self):
    return '({}, {}, {})'.format(self.event_timestamp,
                                 self.processing_time,
                                 self.watermark)


class _WatermarkEventGenerator(beam.DoFn):
  # Used to return the initial timing information.
  EXECUTE_ONCE_STATE = beam.transforms.userstate.BagStateSpec(
      name='execute_once_state',
      coder=beam.coders.FastPrimitivesCoder())
  WATERMARK_TRACKER = TimerSpec('watermark_tracker', TimeDomain.REAL_TIME)

  def __init__(self, sample_resolution_sec=0.1):
    self._sample_resolution_sec = sample_resolution_sec

  @on_timer(WATERMARK_TRACKER)
  def on_watermark_tracker(
      self,
      timestamp=beam.DoFn.TimestampParam,
      window=beam.DoFn.WindowParam,
      watermark_tracker=beam.DoFn.TimerParam(WATERMARK_TRACKER)):
    next_sample_time = timestamp.micros / 1000000 + self._sample_resolution_sec
    watermark_tracker.set(next_sample_time)

    # Generate two events, the delta since the last sample and a place-holder
    # WatermarkEvent. This is a placeholder because we can't otherwise add the
    # watermark from the runner to the event.
    yield ProcessingTimeEvent(self._sample_resolution_sec)
    yield WatermarkEvent(MIN_TIMESTAMP)

  def process(self, e,
              timestamp=beam.DoFn.TimestampParam,
              window=beam.DoFn.WindowParam,
              watermark_tracker=beam.DoFn.TimerParam(WATERMARK_TRACKER),
              execute_once_state=beam.DoFn.StateParam(EXECUTE_ONCE_STATE)):

    _, (element, timing_info) = e

    first_time = next(execute_once_state.read(), True)
    if first_time:
      # Generate the initial timing events.
      execute_once_state.add(False)
      now_sec = timing_info.processing_time.micros / 1000000
      watermark_tracker.set(now_sec + self._sample_resolution_sec)
      yield TestStreamFileHeader()
      yield ProcessingTimeEvent(
          Duration(micros=timing_info.processing_time.micros))
      yield WatermarkEvent(MIN_TIMESTAMP)
    yield element


class _TestStreamEventGenerator(beam.DoFn):
  def start_bundle(self):
    self.elements = []
    self.timing_events = []

  def finish_bundle(self):
    if self.timing_events:
      yield WindowedValue(self.timing_events, timestamp=0,
                          windows=[beam.window.GlobalWindow()])

    if self.elements:
      yield WindowedValue([ElementEvent(self.elements)], timestamp=0,
                          windows=[beam.window.GlobalWindow()])

  def process(self, e, timestamp=beam.DoFn.TimestampParam):
    element, timing_info = e
    if isinstance(element, WatermarkEvent):
      element.new_watermark = timing_info.watermark
      self.timing_events.append(element)
    elif isinstance(element, ProcessingTimeEvent):
      self.timing_events.append(element)
    elif not isinstance(element, TestStreamFileHeader):
      self.elements.append(TimestampedValue(element, timestamp))


class _TestStreamFileRecordGenerator(beam.DoFn):
  def __init__(self, coder):
    self._coder = coder

  def start_bundle(self):
    self.elements = []
    self.timing_events = []

  def finish_bundle(self):
    if self.timing_events:
      for e, processing_time in self.timing_events:
        if isinstance(e, WatermarkEvent):
          watermark_event = TestStreamPayload.Event.AdvanceWatermark(
              new_watermark=int(e.new_watermark))
          processing_time = processing_time.to_proto()
          record = TestStreamFileRecord(watermark_event=watermark_event,
                                        processing_time=processing_time)
          yield WindowedValue(record, timestamp=0,
                              windows=[beam.window.GlobalWindow()])

    if self.elements:
      elements = []
      for tv, processing_time in self.elements:
        element_timestamp = tv.timestamp.micros
        processing_time = processing_time.to_proto()
        element = beam_runner_api_pb2.TestStreamPayload.TimestampedElement(
            encoded_element=self._coder.encode(tv.value),
            timestamp=element_timestamp)
        elements.append(element)

      element_event = TestStreamPayload.Event.AddElements(elements=elements)
      record = TestStreamFileRecord(element_event=element_event,
                                    processing_time=processing_time)
      yield WindowedValue(record, timestamp=0,
                          windows=[beam.window.GlobalWindow()])

  def process(self, e, timestamp=beam.DoFn.TimestampParam):
    element, timing_info = e

    if isinstance(element, WatermarkEvent):
      element.new_watermark = timing_info.watermark
      self.timing_events.append((element, timing_info.processing_time))
    elif isinstance(element, ProcessingTimeEvent):
      self.timing_events.append((element, timing_info.processing_time))
    elif isinstance(element, TestStreamFileHeader):
      yield element
    else:
      self.elements.append((TimestampedValue(element, timestamp),
                            timing_info.processing_time))


class ReverseTestStream(PTransform):
  FILE_RECORD = 'file_record'
  EVENTS = 'events'
  SERIALIZED = 'serialized'

  def __init__(self, sample_resolution_sec, coder=None, output_format=None):
    self._sample_resolution_sec = sample_resolution_sec
    self._output_format = output_format
    self._coder = (coder if coder is not None
                   else beam.coders.FastPrimitivesCoder())

  def expand(self, pcoll):
    generator = (_TestStreamFileRecordGenerator(coder=self._coder)
                 if (self._output_format == ReverseTestStream.FILE_RECORD or
                     self._output_format == ReverseTestStream.SERIALIZED)
                 else _TestStreamEventGenerator())

    ret = (pcoll
           | beam.WindowInto(beam.window.GlobalWindows())
           | 'initial timing' >> _TimingInfoReporter()
           | beam.Map(lambda x: (0, x))
           | beam.ParDo(_WatermarkEventGenerator(
               sample_resolution_sec=self._sample_resolution_sec))
           | 'timing info for watermarks' >> _TimingInfoReporter()
           | beam.ParDo(generator))

    if self._output_format == ReverseTestStream.SERIALIZED:
      def serializer(e):
        return e.SerializeToString()
      ret = ret | 'serializer' >> beam.Map(serializer)

    return ret
