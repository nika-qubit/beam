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

"""Module of mocks for Clusters tests.

Usage:
  from apache_beam.runners.interactive import interactive_beam as ib
  from apache_beam.runners.interactive.dataproc.dataproc_cluster_manager import DataprocClusterManager

  # Context: below tests are in a test class.

  @patch.object(DataprocClusterManager, 'create_flink_cluster')
  @patch.object(DataprocClusterManager, 'cleanup', mock_delete_cluster)
  # Mock the global singleton InteractiveEnvironment if needed.
  @patch('apache_beam.runners.interactive.interactive_environment.current_env')
  def test_clusters_reuse_a_cluster(self, m_env, m_create_cluster):
    # Mock the global singleton clusters instance.
    clusters = ib.Clusters()
    m_env().clusters = clusters
    ...
    # If a cluster should not be created but reused in the test.
    mock_create_cluster.assert_not_called()

  @patch.object(DataprocClusterManager, 'create_flink_cluster',
      mock_create_cluster)
  @patch.object(DataprocClusterManager, 'cleanup', mock_delete_cluster)
  @patch('apache_beam.runners.interactive.interactive_environment.current_env')
  def test_clusters_create_a_new_cluster(self, m_env):
    clusters = ib.Clusters()
    m_env().clusters = clusters
    cluster_metadata = ClusterMetadata(project_id='some-id')
    ...
    # If a new cluster should be created, check the derived metadata are
    # populated.
    self.assertTrue(cluster_metadata.master_url.startswith('test-url'))
    self.assertEqual(cluster_metadata.dashboard, 'test-dashboard')
"""

import uuid


def mock_create_cluster(self):
  """Mocks a cluster creation and populates derived fields."""
  self.cluster_metadata.master_url = 'test-url-' + uuid.uuid4().hex
  self.cluster_metadata.dashboard = 'test-dashboard'


def mock_delete_cluster(self):
  """Mocks a cluster deletion to be NOOP."""
  pass
