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

# pytype: skip-file

from __future__ import absolute_import

import unittest

from apache_beam import coders
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileHeader
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileRecord
from apache_beam.portability.api.beam_runner_api_pb2 import TestStreamPayload
from apache_beam.runners.interactive.caching.streaming_cache import StreamingCache
from apache_beam.runners.interactive.testing.test_cache_manager import FileRecordsBuilder
from apache_beam.runners.interactive.testing.test_cache_manager import InMemoryCache

# Nose automatically detects tests if they match a regex. Here, it mistakens
# these protos as tests. For more info see the Nose docs at:
# https://nose.readthedocs.io/en/latest/writing_tests.html
TestStreamPayload.__test__ = False
TestStreamFileHeader.__test__ = False
TestStreamFileRecord.__test__ = False


class StreamingCacheTest(unittest.TestCase):
  def setUp(self):
    pass

  def test_single_reader(self):
    """Tests that we expect to see all the correctly emitted TestStreamPayloads.
    """
    CACHED_PCOLLECTION_KEY = 'arbitrary key'

    builder = FileRecordsBuilder(tag=CACHED_PCOLLECTION_KEY)
    (builder
     .add_element(
         element=0,
         event_time=0,
         processing_time=0)
     .add_element(
         element=1,
         event_time=1,
         processing_time=1)
     .add_element(
         element=2,
         event_time=2,
         processing_time=2))

    cache = StreamingCache(InMemoryCache())
    cache.write(builder.build(), CACHED_PCOLLECTION_KEY)

    reader, _ = cache.read(CACHED_PCOLLECTION_KEY)
    coder = coders.FastPrimitivesCoder()
    events = list(reader)
    expected = [
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(0),
                    timestamp=0)],
                tag=CACHED_PCOLLECTION_KEY)),
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(1),
                    timestamp=1 * 10**6)],
                tag=CACHED_PCOLLECTION_KEY)),
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(2),
                    timestamp=2 * 10**6)],
                tag=CACHED_PCOLLECTION_KEY)),
    ]
    self.assertSequenceEqual(events, expected)


  def test_multiple_readers(self):
    """Tests that the service advances the clock with multiple outputs."""

    CACHED_LETTERS = 'letters'
    CACHED_NUMBERS = 'numbers'
    CACHED_LATE = 'late'

    letters = FileRecordsBuilder(CACHED_LETTERS)
    (letters
     .advance_watermark(0, 1)
     .add_element(
         element='a',
         event_time=0,
         processing_time=1)
     .advance_watermark(10, 11)
     .add_element(
         element='b',
         event_time=10,
         processing_time=11))

    numbers = FileRecordsBuilder(CACHED_NUMBERS)
    (numbers
     .add_element(
         element=1,
         event_time=0,
         processing_time=2)
     .add_element(
         element=2,
         event_time=0,
         processing_time=3)
     .add_element(
         element=2,
         event_time=0,
         processing_time=4))

    late = FileRecordsBuilder(CACHED_LATE)
    late.add_element(
        element='late',
        event_time=0,
        processing_time=101)

    cache = StreamingCache(InMemoryCache())
    cache.write(letters.build(), CACHED_LETTERS)
    cache.write(numbers.build(), CACHED_NUMBERS)
    cache.write(late.build(), CACHED_LATE)

    reader = cache.read_multiple([CACHED_LETTERS, CACHED_NUMBERS, CACHED_LATE])
    coder = coders.FastPrimitivesCoder()
    events = list(reader)

    expected = [
        # Advances clock from 0 to 1
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            watermark_event=TestStreamPayload.Event.AdvanceWatermark(
                new_watermark=0,
                tag=CACHED_LETTERS)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode('a'),
                    timestamp=0)],
                tag=CACHED_LETTERS)),

        # Advances clock from 1 to 2
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(1),
                    timestamp=0)],
                tag=CACHED_NUMBERS)),

        # Advances clock from 2 to 3
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(2),
                    timestamp=0)],
                tag=CACHED_NUMBERS)),

        # Advances clock from 3 to 4
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=1 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode(2),
                    timestamp=0)],
                tag=CACHED_NUMBERS)),

        # Advances clock from 4 to 11
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=7 * 10**6)),
        TestStreamPayload.Event(
            watermark_event=TestStreamPayload.Event.AdvanceWatermark(
                new_watermark=10 * 10**6,
                tag=CACHED_LETTERS)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode('b'),
                    timestamp=10 * 10**6)],
                tag=CACHED_LETTERS)),

        # Advances clock from 11 to 101
        TestStreamPayload.Event(
            processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
                advance_duration=90 * 10**6)),
        TestStreamPayload.Event(
            element_event=TestStreamPayload.Event.AddElements(
                elements=[TestStreamPayload.TimestampedElement(
                    encoded_element=coder.encode('late'),
                    timestamp=0)],
                tag=CACHED_LATE)),
    ]

    self.assertSequenceEqual(events, expected)


if __name__ == '__main__':
  unittest.main()
