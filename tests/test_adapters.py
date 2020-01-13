# Copyright 2019 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

import vcr

import dimod
from dwave.cloud import Client
from dwave.system import DWaveSampler, FixedEmbeddingComposite
from dwave.embedding import embed_bqm
from dwave.embedding.utils import edgelist_to_adjacency

from dwave.inspector.adapters import (
    from_qmi_response, from_bqm_response, from_bqm_sampleset)


rec = vcr.VCR(
    serializer='yaml',
    cassette_library_dir='tests/fixtures/cassettes',
    record_mode='once',
    match_on=['uri', 'method'],
    filter_headers=['x-auth-token'],
)


class TestAdapters(unittest.TestCase):

    @rec.use_cassette('triangle.yaml')
    def setUp(self):
        with Client.from_config() as client:
            self.solver = client.get_solver(qpu=True)

        self.ising = ({}, {'ab': 1, 'bc': 1, 'ca': 1})
        self.bqm = dimod.BQM.from_ising(*self.ising)
        self.embedding = {'a': [0], 'b': [4], 'c': [1, 5]}

        target_edgelist = [[0, 4], [0, 5], [1, 4], [1, 5]]
        target_adjacency = edgelist_to_adjacency(target_edgelist)
        self.bqm_embedded = embed_bqm(self.bqm, self.embedding, target_adjacency)
        self.problem = (self.bqm_embedded.linear, self.bqm_embedded.quadratic)

    @rec.use_cassette('triangle.yaml')
    def test_from_qmi_response(self):
        # sample
        with Client.from_config() as client:
            solver = client.get_solver(qpu=True)
            response = solver.sample_ising(*self.problem, num_reads=100)

        # convert
        data = from_qmi_response(self.problem, response)

        # validate
        self.assertEqual(data['details']['solver'], solver.id)
        self.assertEqual(sum(data['answer']['num_occurrences']), 100)

    @rec.use_cassette('triangle.yaml')
    def test_from_bqm_response(self):
        # sample
        with Client.from_config() as client:
            solver = client.get_solver(qpu=True)
            response = solver.sample_ising(*self.problem, num_reads=100)

        # convert
        data = from_bqm_response(self.bqm, self.embedding, response)

        # validate
        self.assertEqual(data['details']['solver'], solver.id)
        self.assertEqual(sum(data['answer']['num_occurrences']), 100)

    @rec.use_cassette('triangle.yaml')
    def test_from_bqm_sampleset(self):
        # sample
        qpu = DWaveSampler(solver=dict(qpu=True))
        sampler = FixedEmbeddingComposite(qpu, self.embedding)
        sampleset = sampler.sample(self.bqm, num_reads=100, return_embedding=True)

        # convert
        data = from_bqm_sampleset(self.bqm, sampleset, sampler, self.embedding)

        # validate
        self.assertEqual(data['details']['solver'], qpu.solver.id)
        self.assertEqual(sum(data['answer']['num_occurrences']), 100)

    def test_from_objects(self):
        pass
