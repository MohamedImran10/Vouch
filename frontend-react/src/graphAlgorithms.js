function eligibleEdges(edges, category) {
  if (!category || category === 'all') return edges
  return edges.filter((edge) => edge.category === 'friend' || edge.category === category)
}

function adjacencyFor(edges, category) {
  const adjacency = new Map()
  for (const edge of eligibleEdges(edges, category)) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, [])
    adjacency.get(edge.source).push(edge)
  }
  return adjacency
}

export function breadthFirstSearch(graph, startId, category = 'all') {
  const adjacency = adjacencyFor(graph.edges, category)
  const distance = new Map([[startId, 0]])
  const parent = new Map()
  const order = []
  const queue = [startId]

  for (let index = 0; index < queue.length; index += 1) {
    const current = queue[index]
    order.push(current)
    for (const edge of adjacency.get(current) || []) {
      if (distance.has(edge.target)) continue
      distance.set(edge.target, distance.get(current) + 1)
      parent.set(edge.target, { node: current, edge })
      queue.push(edge.target)
    }
  }

  const nodesById = new Map(graph.nodes.map((node) => [node.id, node]))
  const providers = queue
    .filter((id) => id !== startId && nodesById.get(id)?.type === 'provider')
    .filter((id) => category === 'all' || nodesById.get(id)?.category === category)
    .map((id) => {
      const path = [id]
      let cursor = id
      while (parent.has(cursor)) {
        cursor = parent.get(cursor).node
        path.unshift(cursor)
      }
      return { id, distance: distance.get(id), path }
    })
    .sort((left, right) => left.distance - right.distance)

  return { order, providers, distance, treeEdges: [...parent.values()].map((entry) => entry.edge) }
}

export function depthFirstSearch(graph, startId, targetId, category = 'all') {
  const adjacency = adjacencyFor(graph.edges, category)
  const visited = new Set()
  const active = new Set()
  const path = []
  let cycleDetected = false

  function visit(nodeId) {
    if (active.has(nodeId)) {
      cycleDetected = true
      return false
    }
    if (visited.has(nodeId)) return false
    visited.add(nodeId)
    active.add(nodeId)
    path.push(nodeId)
    if (nodeId === targetId) return true

    for (const edge of adjacency.get(nodeId) || []) {
      if (visit(edge.target)) return true
    }

    path.pop()
    active.delete(nodeId)
    return false
  }

  const found = visit(startId)
  return { found, path: found ? path : [], visited: [...visited], cycleDetected }
}
