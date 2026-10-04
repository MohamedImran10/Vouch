import { useEffect, useMemo, useRef, useState } from 'react'
import {
  forceCenter,
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
} from 'd3-force'
import { Focus, GitBranch, RotateCcw, Users } from 'lucide-react'

const colors = {
  user: '#4e9675',
  provider: '#6085ad',
  root: '#e46f4b',
  friend: '#87938c',
  plumber: '#559b85',
  mechanic: '#bc9a48',
  electrician: '#d27651',
  babysitter: '#8b83ab',
  cleaner: '#708fad',
}

function displayName(node, providers, rootId) {
  if (node.id === rootId) return 'You'
  const provider = providers.find((item) => item.id === node.id)
  if (provider) return provider.name
  return node.label || node.id.replace(/[_-]+/g, ' ')
}

export default function NetworkGraph({
  nodes,
  edges,
  providers,
  rootId,
  category,
  activeEdgeKeys,
  visitOrder,
  selectedNode,
  onSelectNode,
}) {
  const containerRef = useRef(null)
  const [size, setSize] = useState({ width: 920, height: 560 })
  const [positions, setPositions] = useState([])
  const providerIds = useMemo(() => new Set(edges.filter((edge) => edge.category !== 'friend').map((edge) => edge.target)), [edges])
  const activeEdges = useMemo(() => new Set(activeEdgeKeys), [activeEdgeKeys])
  const visits = useMemo(() => new Set(visitOrder), [visitOrder])

  useEffect(() => {
    const element = containerRef.current
    if (!element) return undefined
    const observer = new ResizeObserver(([entry]) => {
      setSize({ width: Math.max(entry.contentRect.width, 320), height: Math.max(entry.contentRect.height, 400) })
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  useEffect(() => {
    if (!nodes.length) return undefined
    const centerX = size.width / 2
    const centerY = size.height / 2
    const simulationNodes = nodes.map((node, index) => {
      const angle = (index / nodes.length) * Math.PI * 2
      const radius = Math.min(size.width, size.height) * 0.3
      return { ...node, x: centerX + Math.cos(angle) * radius, y: centerY + Math.sin(angle) * radius }
    })
    const simulationEdges = edges.map((edge) => ({ ...edge }))
    const simulation = forceSimulation(simulationNodes)
      .force('link', forceLink(simulationEdges).id((node) => node.id).distance(118).strength(0.42))
      .force('charge', forceManyBody().strength(-360))
      .force('center', forceCenter(centerX, centerY))
      .force('x', forceX(centerX).strength(0.08))
      .force('y', forceY(centerY).strength(0.08))
      .force('collide', forceCollide(38))
      .on('tick', () => {
        const marginX = Math.min(82, centerX - 30)
        const marginY = Math.min(52, centerY - 28)
        for (const node of simulationNodes) {
          node.x = Math.max(marginX, Math.min(size.width - marginX, node.x))
          node.y = Math.max(marginY, Math.min(size.height - marginY, node.y))
        }
        setPositions(simulationNodes.map((node) => ({ id: node.id, x: node.x, y: node.y })))
      })
    return () => simulation.stop()
  }, [nodes, edges, size])

  const positionMap = new Map(positions.map((position) => [position.id, position]))
  const visitOrderMap = new Map(visitOrder.map((id, index) => [id, index + 1]))

  return (
    <div className="graph-canvas" ref={containerRef}>
      {nodes.length === 0 ? (
        <div className="graph-empty"><Users size={30} /><strong>No connections yet</strong><span>Add your first vouch to start the network.</span></div>
      ) : (
        <svg className="network-svg" viewBox={`0 0 ${size.width} ${size.height}`} role="img" aria-label="Interactive trust network graph">
          <defs>
            <pattern id="graph-grid" width="24" height="24" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="1" fill="#c8cec8" opacity=".48" />
            </pattern>
          </defs>
          <rect width={size.width} height={size.height} fill="url(#graph-grid)" />
          {edges.map((edge, index) => {
            const source = positionMap.get(edge.source)
            const target = positionMap.get(edge.target)
            if (!source || !target) return null
            const key = `${edge.source}->${edge.target}`
            const isActive = activeEdges.has(key)
            const isVisited = visits.has(edge.source) && visits.has(edge.target)
            const isVisibleCategory = category === 'all' || edge.category === category || edge.category === 'friend'
            const edgeColor = edge.category === 'friend' ? colors.friend : colors[edge.category] || '#aeb5ae'
            return (
              <g key={`${key}-${index}`} className={isActive ? 'graph-edge active' : isVisited ? 'graph-edge visited' : 'graph-edge'}>
                <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} stroke={isActive ? '#e46f4b' : edgeColor} opacity={isVisibleCategory ? (category === 'all' || edge.category === category ? 0.66 : 0.22) : 0.08} />
                <title>{`${displayName({ id: edge.source }, providers, rootId)} vouched for ${displayName({ id: edge.target }, providers, rootId)} · ${edge.category}`}</title>
              </g>
            )
          })}
          {positions.map((position) => {
            const node = nodes.find((item) => item.id === position.id)
            if (!node) return null
            const isRoot = node.id === rootId
            const isProvider = providerIds.has(node.id)
            const fill = isRoot ? colors.root : isProvider ? colors.provider : colors.user
            const selected = selectedNode === node.id
            const visited = visitOrderMap.has(node.id)
            return (
              <g
                className={`graph-node${selected ? ' selected' : ''}${visited ? ' visited' : ''}`}
                key={node.id}
                onClick={() => onSelectNode(node.id)}
                role="button"
                tabIndex="0"
                onKeyDown={(event) => (event.key === 'Enter' || event.key === ' ') && onSelectNode(node.id)}
                transform={`translate(${position.x},${position.y})`}
              >
                <title>{`${displayName(node, providers, rootId)}${visited ? ` · traversal ${visitOrderMap.get(node.id)}` : ''}`}</title>
                <circle className="node-halo" r={selected ? 30 : 25} fill={fill} />
                <circle className="node-core" r={isRoot ? 18 : 15} fill={fill} />
                <text className="node-initial" y="4">{displayName(node, providers, rootId).slice(0, 1).toUpperCase()}</text>
                <text className="node-label" y="36">{displayName(node, providers, rootId).length > 17 ? `${displayName(node, providers, rootId).slice(0, 16)}…` : displayName(node, providers, rootId)}</text>
                {visited && <text className="visit-number" x="18" y="-17">{visitOrderMap.get(node.id)}</text>}
              </g>
            )
          })}
        </svg>
      )}
      <div className="graph-legend" aria-label="Node legend">
        <span><i style={{ background: colors.root }} />You</span>
        <span><i style={{ background: colors.user }} />People</span>
        <span><i style={{ background: colors.provider }} />Providers</span>
      </div>
      <div className="graph-hint"><Focus size={14} /> Select a node to inspect or trace a path</div>
      <button className="graph-reset" title="Reset graph layout" onClick={() => setSize((current) => ({ ...current }))}><RotateCcw size={15} /></button>
      <span className="graph-count"><GitBranch size={14} /> {nodes.length} people · {edges.length} links</span>
    </div>
  )
}
