import logging
import time

from concurrent.futures import ThreadPoolExecutor

import grpc

from apache_beam.portability.api import beam_runner_api_pb2
from apache_beam.portability.api import beam_runner_api_pb2_grpc
from apache_beam.portability.api.beam_runner_api_pb2 import TestStreamPayload
from apache_beam.portability.api.beam_runner_api_pb2_grpc import TestStreamServiceServicer

class ATestStreamServiceServicer(TestStreamServiceServicer):
  def Events(self, request, context):
    element = TestStreamPayload.Event()
    element.element_event.elements.append(
        TestStreamPayload.TimestampedElement(timestamp=int(time.time())))
    yield element

class BTestStreamServiceServicer(TestStreamServiceServicer):
  def Events(self, request, context):
    element = TestStreamPayload.Event()
    element.element_event.elements.append(
        TestStreamPayload.TimestampedElement(timestamp=0))
    yield element

def build_server():
  server = grpc.server(ThreadPoolExecutor(max_workers=10))
  port = server.add_insecure_port('[::]:0')
  logging.warning('Port selected is {}'.format(port))
  # The endpoint is selected during server construction time. So if the client
  # connects lazily, they can use the returned value even before the server is
  # started.
  endpoint = '[::]:{}'.format(port)
  # This can be added after the server is started and still works. Weird.
  beam_runner_api_pb2_grpc.add_TestStreamServiceServicer_to_server(
      ATestStreamServiceServicer(),
      server)
  return server, endpoint

def connect_to_server(endpoint):
  channel = grpc.insecure_channel(endpoint)
  return beam_runner_api_pb2_grpc.TestStreamServiceStub(channel)

try:
  server, endpoint = build_server()
  server.start()
  stub = connect_to_server(endpoint)
  event_payload = stub.Events(beam_runner_api_pb2.EventsRequest())
  logging.warning(next(event_payload))
  # Though you can add servicer during runtime through the weirdness of python,
  # the second servicer wouldn't be taken by the server.
  beam_runner_api_pb2_grpc.add_TestStreamServiceServicer_to_server(
      BTestStreamServiceServicer(),
      server)
  event_payload = stub.Events(beam_runner_api_pb2.EventsRequest())
  # You will not see timestamp==0 here. The implementation is still
  # ATestStreamServiceServicer.
  logging.warning(next(event_payload))
  # Whatever waiting logic here to keep the server running before exiting. Then
  # play with the server from other client thread and channels.
  time.sleep(5)
finally:
  server.stop(0)
  server.wait_for_termination()
