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

import itertools
import os
import shutil
import tempfile
import time

import apache_beam as beam
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileHeader
from apache_beam.portability.api.beam_interactive_api_pb2 import TestStreamFileRecord
from apache_beam.portability.api.beam_runner_api_pb2 import TestStreamPayload
from apache_beam.runners.interactive.cache_manager import CacheManager
from apache_beam.runners.interactive.cache_manager import SafeFastPrimitivesCoder
from apache_beam.testing.test_stream import ReverseTestStream
from apache_beam.utils import timestamp
from apache_beam.utils.timestamp import Timestamp


class StreamingCacheSink(beam.PTransform):
  def __init__(self, cache_dir, filename, sample_resolution_sec,
               coder=SafeFastPrimitivesCoder()):
    self._cache_dir = cache_dir
    self._filename = filename
    self._sample_resolution_sec = sample_resolution_sec
    self._coder = coder

  def expand(self, pcoll):
    # Note that this assumes that the elements are ordered, so it only works on
    # the DirectRunner.

    # This is broken in a number of different ways:
    #  * Assumes elements come in ordered
    #  * Assumes that there is only one machine doing the writing
    #
    class StreamingWriteToText(beam.DoFn):
      def __init__(self, path, filename, coder=SafeFastPrimitivesCoder()):
        self._path = path
        self._filename = filename
        self._full_path = os.path.join(self._path, self._filename)
        self.coder = coder

        if not os.path.exists(self._path):
          os.makedirs(self._path)

      def start_bundle(self):
        self._fh = open(self._full_path, 'ab')

      def finish_bundle(self):
        self._fh.close()

      def process(self, e):
        self._fh.write(self.coder.encode(e))
        self._fh.write(b'\n')

    return (pcoll
            | ReverseTestStream(
                output_tag=self._filename,
                sample_resolution_sec=self._sample_resolution_sec,
                output_format=ReverseTestStream.SERIALIZED,
                coder=self._coder)
            | beam.ParDo(StreamingWriteToText(path=self._cache_dir,
                                              filename=self._filename,
                                              coder=self._coder))
            )


class StreamingCacheSource:
  def __init__(self, cache_dir, labels, is_cache_complete=None,
               coder=SafeFastPrimitivesCoder()):
    self._cache_dir = cache_dir
    self._coder = coder
    self._labels = labels
    self._is_cache_complete = (is_cache_complete
                               if is_cache_complete
                               else lambda: True)

  def _wait_until_file_exists(self, timeout_secs=30):
    f = None
    now_secs = time.time()
    timeout_timestamp_secs = now_secs + timeout_secs
    while f is None and now_secs < timeout_timestamp_secs:
      now_secs = time.time()
      try:
        path = os.path.join(self._cache_dir, *self._labels)
        f = open(path, mode='r')
      except EnvironmentError as e:
        # For Python2 and Python3 compatibility, this checks the
        # EnvironmentError to see if the file exists.
        # TODO: Change this to a FileNotFoundError when Python3 migration is
        # complete.
        import errno
        if e.errno != errno.ENOENT:
          # Raise the exception if it is not a FileNotFoundError.
          raise
        time.sleep(1)
    if now_secs >= timeout_timestamp_secs:
      raise RuntimeError(
          "Timed out waiting for file '{}' to be available".format(path))
    return f

  def _emit_from_file(self, fh, tail):
    # Always read at least once to read the whole file.
    while True:
      pos = fh.tell()
      line = fh.readline()

      # Check if we are at EOF.
      if not line:
        # Complete reading only when the cache is complete.
        if self._is_cache_complete():
          break

        if not tail:
          break

        # Otherwise wait for new data in the file to be written.
        time.sleep(0.5)
        fh.seek(pos)
      else:
        # The first line at pos = 0 is always the header. Read the line without
        # the new line.
        if pos == 0:
          header = TestStreamFileHeader()
          header.ParseFromString(self._coder.decode(line[:-1]))
          yield header
        else:
          record = TestStreamFileRecord()
          record.ParseFromString(self._coder.decode(line[:-1]))
          yield record

  def read(self, tail):
    with self._wait_until_file_exists() as f:
      for e in self._emit_from_file(f, tail):
        yield e


class StreamingCache(CacheManager):
  """Abstraction that holds the logic for reading and writing to cache.
  """
  def __init__(self, cache_dir, is_cache_complete=None,
               sample_resolution_sec=0.1):
    self._sample_resolution_sec = sample_resolution_sec
    self._is_cache_complete = is_cache_complete

    if cache_dir:
      self._cache_dir = cache_dir
    else:
      self._cache_dir = tempfile.mkdtemp(
          prefix='interactive-temp-', dir=os.environ.get('TEST_TMPDIR', None))

    # List of saved pcoders keyed by PCollection path. It is OK to keep this
    # list in memory because once FileBasedCacheManager object is
    # destroyed/re-created it loses the access to previously written cache
    # objects anyways even if cache_dir already exists. In other words,
    # it is not possible to resume execution of Beam pipeline from the
    # saved cache if FileBasedCacheManager has been reset.
    #
    # However, if we are to implement better cache persistence, one needs
    # to take care of keeping consistency between the cached PCollection
    # and its PCoder type.
    self._saved_pcoders = {}
    self._default_pcoder = SafeFastPrimitivesCoder()

  def exists(self, *labels):
    path = os.path.join(self._cache_dir, *labels)
    return os.path.exists(path)

  # TODO(srohde): Modify this to return the correct version.
  def read(self, *labels):
    if not self.exists(*labels):
      return itertools.chain([]), -1

    reader = StreamingCacheSource(
        self._cache_dir, labels,
        is_cache_complete=self._is_cache_complete).read(tail=False)
    header = next(reader)
    return StreamingCache.Reader([header], [reader]).read(), 1

  def read_multiple(self, labels):
    readers = [
        StreamingCacheSource(self._cache_dir, l,
                             is_cache_complete=self._is_cache_complete)
        .read(tail=True) for l in labels]
    headers = [next(r) for r in readers]
    return StreamingCache.Reader(headers, readers).read()

  def write(self, values, *labels):
    to_write = [v.SerializeToString() for v in values]
    directory = os.path.join(self._cache_dir, *labels[:-1])
    filepath = os.path.join(directory, labels[-1])
    if not os.path.exists(directory):
      os.makedirs(directory)
    with open(filepath, 'ab') as f:
      for line in to_write:
        f.write(self._default_pcoder.encode(line))
        f.write(b'\n')

  def source(self, *labels):
    return beam.Impulse()

  def sink(self, *labels):
    filename = labels[-1]
    cache_dir = os.path.join(self._cache_dir, *labels[:-1])
    return StreamingCacheSink(cache_dir, filename, self._sample_resolution_sec)

  def save_pcoder(self, pcoder, *labels):
    self._saved_pcoders[os.path.join(*labels)] = pcoder

  def load_pcoder(self, *labels):
    return (self._default_pcoder if self._default_pcoder is not None else
            self._saved_pcoders[os.path.join(*labels)])

  def cleanup(self):
    if os.path.exists(self._cache_dir):
      shutil.rmtree(self._cache_dir)
    self._saved_pcoders = {}

  class Reader(object):
    """Abstraction that reads from PCollection readers.

    This class is an Abstraction layer over multiple PCollection readers to be
    used for supplying a TestStream service with events.

    This class is also responsible for holding the state of the clock, injecting
    clock advancement events, and watermark advancement events.
    """
    def __init__(self, headers, readers):
      # This timestamp is used as the monotonic clock to order events in the
      # replay.
      self._monotonic_clock = timestamp.Timestamp.of(0)

      # The PCollection cache readers.
      self._readers = {}

      # The file headers that are metadata for that particular PCollection.
      # The header allows for metadata about an entire stream, so that the data
      # isn't copied per record.
      self._headers = {header.tag : header for header in headers}
      self._readers = {h.tag : r for (h, r) in zip(headers, readers)}

      # The watermarks per tag. Useful for introspection in the stream.
      self._watermarks = {tag: timestamp.MIN_TIMESTAMP for tag in self._headers}

      # The most recently read timestamp per tag.
      self._stream_times = {
          tag: timestamp.MIN_TIMESTAMP
          for tag in self._headers
      }

    def _test_stream_events_before_target(self, target_timestamp):
      """Reads the next iteration of elements from each stream.

      Retrieves an element from each stream iff the most recently read timestamp
      from that stream is less than the target_timestamp. Since the amount of
      events may not fit into memory, this StreamingCache reads at most one
      element from each stream at a time.
      """
      records = []
      for tag, r in self._readers.items():
        # The target_timestamp is the maximum timestamp that was read from the
        # stream. Some readers may have elements that are less than this. Thus,
        # we skip all readers that already have elements that are at this
        # timestamp so that we don't read everything into memory.
        if self._stream_times[tag] >= target_timestamp:
          continue
        try:
          record = next(r)
          records.append((tag, record))
          self._stream_times[tag] = Timestamp.from_proto(record.processing_time)
        except StopIteration:
          pass
      return records

    def _merge_sort(self, previous_events, new_events):
      return sorted(
          previous_events + new_events,
          key=lambda x: Timestamp.from_proto(x[1].processing_time),
          reverse=True)

    def _min_timestamp_of(self, events):
      return (
          Timestamp.from_proto(events[-1][1].processing_time)
          if events else timestamp.MAX_TIMESTAMP)

    def _event_stream_caught_up_to_target(self, events, target_timestamp):
      empty_events = not events
      stream_is_past_target = self._min_timestamp_of(events) > target_timestamp
      return empty_events or stream_is_past_target

    def read(self):
      """Reads records from PCollection readers.
      """

      # The largest timestamp read from the different streams.
      target_timestamp = timestamp.Timestamp.of(0)

      # The events from last iteration that are past the target timestamp.
      unsent_events = []

      # Emit events until all events have been read.
      while True:
        # Read the next set of events. The read events will most likely be
        # out of order if there are multiple readers. Here we sort them into
        # a more manageable state.
        new_events = self._test_stream_events_before_target(target_timestamp)
        events_to_send = self._merge_sort(unsent_events, new_events)
        if not events_to_send:
          break

        # Get the next largest timestamp in the stream. This is used as the
        # timestamp for readers to "catch-up" to. This will only read from
        # readers with a timestamp less than this.
        target_timestamp = self._min_timestamp_of(events_to_send)

        # Loop through the elements with the correct timestamp.
        while not self._event_stream_caught_up_to_target(events_to_send,
                                                         target_timestamp):
          tag, r = events_to_send.pop()

          # First advance the clock to match the time of the stream. This has
          # a side-effect of also advancing this cache's clock.
          curr_timestamp = Timestamp.from_proto(r.processing_time)
          if curr_timestamp > self._monotonic_clock:
            yield self._advance_processing_time(curr_timestamp)

          # Then, send either a new element or watermark.
          if r.HasField('element_event'):
            r.element_event.tag = tag
            yield TestStreamPayload.Event(element_event=r.element_event)
          elif r.HasField('watermark_event'):
            self._watermarks[tag] = timestamp.Timestamp(
                r.watermark_event.new_watermark)
            r.watermark_event.tag = tag
            yield TestStreamPayload.Event(watermark_event=r.watermark_event)
        unsent_events = events_to_send
        target_timestamp = self._min_timestamp_of(unsent_events)

    def _advance_processing_time(self, new_timestamp):
      """Advances the internal clock and returns an AdvanceProcessingTime event.
      """
      advancy_by = new_timestamp.micros - self._monotonic_clock.micros
      e = TestStreamPayload.Event(
          processing_time_event=TestStreamPayload.Event.AdvanceProcessingTime(
              advance_duration=advancy_by))
      self._monotonic_clock = new_timestamp
      return e
