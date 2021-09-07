import logging

import names
import typing

import apache_beam as beam

from apache_beam.runners.interactive import interactive_beam as ib
from apache_beam.runners.interactive import interactive_runner as ir
from apache_beam.options import pipeline_options
from apache_beam.transforms.sql import SqlTransform
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import SetupOptions
import google.auth
from apache_beam.runners.portability import expansion_service
from apache_beam.runners.interactive.sql import beam_sql_magics as beam_sql
from apache_beam.runners.interactive.sql import utils as beam_sql_utils


#### Batch ####
#p = beam.Pipeline(ir.InteractiveRunner())
#
#class Person(typing.NamedTuple):
#    id: int
#    name: str
#
#
#beam_sql_utils.register_coder_for_schema(Person)
#
#persons = (p | beam.Create(range(10))
#           | beam.Map(lambda x: Person(id=x, name=names.get_full_name())).with_output_types(Person))
#
#ib.watch({'persons': persons})
#
#query = 'SELECT * FROM persons where id < 5'
#output1 = beam_sql.apply_sql(query, None, beam_sql_utils.find_pcolls(query, {'persons': persons}))
#
#output1 | 'print person' >> beam.Map(print)
#
#output1.pipeline.run()

#### Streaming ####

logging.root.setLevel(logging.ERROR)
# Setting up the Apache Beam pipeline options.
options = pipeline_options.PipelineOptions()

# Sets the pipeline mode to streaming, so we can stream the data from PubSub.
options.view_as(pipeline_options.StandardOptions).streaming = True

# Sets the project to the default project in your current Google Cloud environment.
# The project will be used for creating a subscription to the Pub/Sub topic.
_, options.view_as(GoogleCloudOptions).project = google.auth.default()

options.view_as(SetupOptions).sdk_location = 'dist/apache-beam-2.34.0.dev0.tar.gz'

p2 = beam.Pipeline(ir.InteractiveRunner(), options=options)

# The Google Cloud PubSub topic for this example.
topic = "projects/pubsub-public-data/topics/shakespeare-kinglear"

ib.options.recording_duration = '20s'

words_bytes = p2 | "read" >> beam.io.ReadFromPubSub(topic=topic)

windowed_words = (words_bytes
                  | "window" >> beam.WindowInto(beam.window.FixedWindows(10)))


class Word(typing.NamedTuple):
    word: str


beam_sql_utils.register_coder_for_schema(Word)


class ParseWordsFromPubsub(beam.DoFn):

    def process(self, e: bytes) -> typing.Iterator[Word]:
        yield Word(word=e.decode('utf-8'))


words = windowed_words | beam.ParDo(ParseWordsFromPubsub()).with_output_types(Word)
ib.watch(locals())


query = 'SELECT * FROM words'
output = beam_sql.apply_sql(query, None, beam_sql_utils.find_pcolls(query, {'words': words}))

output | beam.Map(print)

output.pipeline.run()