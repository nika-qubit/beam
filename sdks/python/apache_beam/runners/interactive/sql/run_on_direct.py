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

"""Module to support running beam_sql_magics on DirectRunner."""

def run_on_direct_runner(query, output_name, found, schemas):
  from apache_beam.runners.interactive.sql.beam_sql_magics import apply_sql
  from apache_beam.runners.interactive.sql.beam_sql_magics import cache_output
  from apache_beam.runners.interactive.sql.beam_sql_magics import collect_data_for_interactive_run

  collect_data_for_interactive_run(query, found)
  output_name, output, chain = apply_sql(query, output_name, found)
  chain.current.schemas = schemas
  cache_output(output_name, output)
  return output

