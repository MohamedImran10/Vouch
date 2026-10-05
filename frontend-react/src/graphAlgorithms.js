function eligibleEdges(edges, category) {
  const normalizedCategory = category?.trim().toLowerCase()
  if (!normalizedCategory || normalizedCategory === 'all' || normalizedCategory === 'every category') return edges
  return edges.filter((edge) => edge.category?.toLowerCase() === 'friend' || edge.category?.toLowerCase() === normalizedCategory)
}

function includesAllCategories(category) {
  const normalizedCategory = category?.trim().toLowerCase()
  return !normalizedCategory || normalizedCategory === 'all' || normalizedCategory === 'every category'
}

export function buildAdjacencyList(edges, category = 'all') {
  const adjacency = new Map()
  for (const edge of eligibleEdges(edges, category)) {
    if (!adjacency.has(edge.source)) adjacency.set(edge.source, [])
    adjacency.get(edge.source).push(edge)
    if (edge.target !== edge.source) {
      if (!adjacency.has(edge.target)) adjacency.set(edge.target, [])
      adjacency.get(edge.target).push({ ...edge, source: edge.target, target: edge.source })
    }
  }
  return adjacency
}

function weakComponentFor(graph, startId, category) {
  const edges = eligibleEdges(graph.edges, category)
  const component = new Set([startId])
  const queue = [startId]
  for (let index = 0; index < queue.length; index += 1) {
    const current = queue[index]
    for (const edge of edges) {
      const neighbor = edge.source === current ? edge.target : edge.target === current ? edge.source : null
      if (neighbor && !component.has(neighbor)) {
        component.add(neighbor)
        queue.push(neighbor)
      }
    }
  }
  return component
}

export function breadthFirstSearch(graph, startId, category = 'all', targetId = '', adjacency = buildAdjacencyList(graph.edges, category)) {
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

  const targetExists = graph.nodes.some((node) => node.id === targetId)
  const isDisconnected = Boolean(targetId && targetExists && !weakComponentFor(graph, startId, category).has(targetId))

  return {
    order,
    providers,
    distance,
    targetPath,
    treeEdges: [...parent.values()].map((entry) => entry.edge),
    reachable: !targetId || targetPath.length > 0,
    reason: isDisconnected ? 'DISCONNECTED_COMPONENT' : targetId && !targetExists ? 'NODE_NOT_FOUND' : targetId && !targetPath.length ? 'NO_DIRECTED_PATH' : null,
  }
}

export function depthFirstSearch(graph, startId, targetId, category = 'all', adjacency = buildAdjacencyList(graph.edges, category)) {
  const targetExists = graph.nodes.some((node) => node.id === targetId)
  if (!targetExists) return { found: false, path: [], visited: [], cycleDetected: false, reachable: false, reason: 'NODE_NOT_FOUND' }
  if (!weakComponentFor(graph, startId, category).has(targetId)) {
    return { found: false, path: [], visited: [], cycleDetected: false, reachable: false, reason: 'DISCONNECTED_COMPONENT' }
  }

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
  return {
    found,
    path: found ? path : [],
    visited: [...visited],
    cycleDetected,
    reachable: found,
    reason: found ? null : 'NO_DIRECTED_PATH',
  }
}
