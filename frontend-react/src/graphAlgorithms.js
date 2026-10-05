function eligibleEdges(edges, category) {
  const normalizedCategory = category?.trim().toLowerCase()
  if (!normalizedCategory || normalizedCategory === 'all' || normalizedCategory === 'every category') return edges
  return edges.filter((edge) => edge.category?.toLowerCase() === 'friend' || edge.category?.toLowerCase() === normalizedCategory)
}

function includesAllCategories(category) {
  const normalizedCategory = category?.trim().toLowerCase()
  return !normalizedCategory || normalizedCategory === 'all' || normalizedCategory === 'every category'
}

function adjacencyFor(edges, category) {
  const adjacency = new Map()
  for (const edge of eligibleEdges(edges, category)) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, [])
    adjacency.get(edge.source).push(edge)
  }
  return adjacency
}

export function breadthFirstSearch(graph, startId, category = 'all', targetId = '') {
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
    .filter((id) => includesAllCategories(category) || nodesById.get(id)?.category?.toLowerCase() === category.trim().toLowerCase())
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

  const targetPath = []
  let cursor = targetId
  while (targetId && distance.has(cursor)) {
    targetPath.unshift(cursor)
    if (cursor === startId) break
    cursor = parent.get(cursor)?.node
    if (!cursor) targetPath.length = 0
  }

  return {
    order,
    providers,
    distance,
    targetPath,
    treeEdges: [...parent.values()].map((entry) => entry.edge),
  }
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
