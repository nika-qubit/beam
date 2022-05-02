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

def run_on_dataflow_runner(query, output_name, found, schemas):
  from apache_beam.runners.interactive.sql.utils import DataflowOptionsForm

  output_name, current_node, chain = apply_sql(
        query, output_name, found, False)
  current_node.schemas = schemas
  _ = chain.to_pipeline()
  _ = DataflowOptionsForm(
      output_name, pcoll_by_name()[output_name],
      verbose).display_for_input()
  return None


