import test from 'node:test'
import assert from 'node:assert/strict'
import { breadthFirstSearch, depthFirstSearch } from './graphAlgorithms.js'

const graph = {
  nodes: [
    { id: 'alice', type: 'user' },
    { id: 'carol', type: 'user' },
    { id: 'bob_plumber', type: 'provider', category: 'plumber' },
    { id: 'eve_plumber', type: 'provider', category: 'plumber' },
    { id: 'dave_mechanic', type: 'provider', category: 'mechanic' },
  ],
  edges: [
    { source: 'alice', target: 'bob_plumber', category: 'plumber' },
    { source: 'alice', target: 'carol', category: 'friend' },
    { source: 'carol', target: 'eve_plumber', category: 'plumber' },
    { source: 'carol', target: 'dave_mechanic', category: 'mechanic' },
  ],
}

test('BFS ranks same-category providers by trust distance', () => {
  const result = breadthFirstSearch(graph, 'alice', 'plumber')
  assert.deepEqual(result.providers, [
    { id: 'bob_plumber', distance: 1, path: ['alice', 'bob_plumber'] },
    { id: 'eve_plumber', distance: 2, path: ['alice', 'carol', 'eve_plumber'] },
  ])
})

test('BFS returns the shortest path to the selected target', () => {
  const result = breadthFirstSearch(graph, 'alice', 'all', 'carol')
  assert.deepEqual(result.targetPath, ['alice', 'carol'])
})

test('BFS leaves the target path empty when the target is unreachable', () => {
  const result = breadthFirstSearch(graph, 'alice', 'plumber', 'dave_mechanic')
  assert.deepEqual(result.targetPath, [])
})

test('DFS returns an exact category-aware trust path', () => {
  const result = depthFirstSearch(graph, 'alice', 'eve_plumber', 'plumber')
  assert.equal(result.found, true)
  assert.deepEqual(result.path, ['alice', 'carol', 'eve_plumber'])
})

test('DFS treats all-category labels case-insensitively', () => {
  for (const category of ['all', 'ALL', 'Every category']) {
    const result = depthFirstSearch(graph, 'alice', 'dave_mechanic', category)
    assert.equal(result.found, true)
    assert.deepEqual(result.path, ['alice', 'carol', 'dave_mechanic'])
  }
})

test('DFS follows the first deep branch while BFS returns the shorter route', () => {
  const multiRouteGraph = {
    nodes: [
      { id: 'alice', type: 'person' },
      { id: 'bob', type: 'provider', category: 'plumber' },
      { id: 'carol', type: 'person' },
      { id: 'grace', type: 'provider', category: 'electrician' },
    ],
    edges: [
      { source: 'alice', target: 'bob', category: 'plumber' },
      { source: 'bob', target: 'carol', category: 'friend' },
      { source: 'carol', target: 'grace', category: 'electrician' },
      { source: 'alice', target: 'grace', category: 'electrician' },
    ],
  }

  const bfsResult = breadthFirstSearch(multiRouteGraph, 'alice', 'all', 'grace')
  const dfsResult = depthFirstSearch(multiRouteGraph, 'alice', 'grace', 'all')

  assert.deepEqual(bfsResult.targetPath, ['alice', 'grace'])
  assert.deepEqual(dfsResult.path, ['alice', 'bob', 'carol', 'grace'])
})

test('DFS reports a missing target without inventing a path', () => {
  const result = depthFirstSearch(graph, 'alice', 'dave_mechanic', 'plumber')
  assert.equal(result.found, false)
  assert.deepEqual(result.path, [])
})
