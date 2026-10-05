import { Component, useEffect, useState } from 'react'
import {
  ArrowDownRight,
  ArrowUpRight,
  ChevronDown,
  CircleHelp,
  Compass,
  GitBranch,
  Heart,
  LogOut,
  Network,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Users,
  X,
} from 'lucide-react'
import { api, getAccessToken, saveAccessToken } from './api'
import NetworkGraph from './NetworkGraph'
import VouchForm from './VouchForm'
import { breadthFirstSearch, depthFirstSearch } from './graphAlgorithms'
import './App.css'

const userStorageKey = 'vouch.currentUser'

class GraphErrorBoundary extends Component {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return <div className="graph-empty" role="alert"><strong>Unable to render graph path</strong><span>Try selecting the destination again.</span></div>
    }
    return this.props.children
  }
}

function readSession() {
  const token = getAccessToken()
  const storedUser = localStorage.getItem(userStorageKey)
  if (!token || !storedUser) return null
  try {
    return { token, user: JSON.parse(storedUser) }
  } catch {
    return null
  }
}

function nameFromId(id = '') {
  return id.replace(/[_-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function initials(name = 'Vouch') {
  return name.trim().split(/\s+/).slice(0, 2).map((word) => word[0]).join('').toUpperCase()
}

function formatDate(value) {
  if (!value) return 'Recently'
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(date)
}

function categoryTitle(id, categories) {
  return categories.find((category) => category.id === id)?.name || nameFromId(id)
}

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('alice@example.com')
  const [password, setPassword] = useState('vouch-demo')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      await onLogin(email, password)
    } catch (loginError) {
      setError(loginError.message || 'Could not connect to Vouch.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-page">
      <div className="login-brand"><span className="brand-mark">v</span><span>vouch</span></div>
      <section className="login-card">
        <div className="login-art" aria-hidden="true">
          <div className="orbit orbit-one" /><div className="orbit orbit-two" />
          <span className="art-dot dot-one" /><span className="art-dot dot-two" /><span className="art-dot dot-three" />
          <div className="art-center"><Heart size={28} fill="currentColor" /></div>
          <span className="art-label label-one">Alice</span><span className="art-label label-two">Dave</span><span className="art-label label-three">You</span>
        </div>
        <div className="login-content">
          <span className="eyebrow">TRUST HAS A WAY OF TRAVELING</span>
          <h1>Good people,<br />closer together.</h1>
          <p>Keep the recommendations you trust, and see the people behind them.</p>
          <form onSubmit={submit}>
            <label className="field-label" htmlFor="login-email">Email address</label>
            <input autoComplete="username" id="login-email" onChange={(event) => setEmail(event.target.value)} type="email" value={email} required />
            <label className="field-label" htmlFor="login-password">Password</label>
            <input autoComplete="current-password" id="login-password" onChange={(event) => setPassword(event.target.value)} type="password" value={password} required />
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary login-submit" disabled={busy} type="submit">
              {busy ? <span className="spinner" /> : <Compass size={17} />}
              {busy ? 'Connecting…' : 'Enter your network'}
            </button>
          </form>
          <div className="demo-note"><Sparkles size={15} /><span>Demo access is ready. Sign in with the prefilled account.</span></div>
        </div>
      </section>
      <p className="login-footnote">A small circle. A much better search.</p>
    </main>
  )
}

function Sidebar({ view, onNavigate, user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="brand-lockup"><span className="brand-mark">v</span><span>vouch</span><span className="brand-period">.</span></div>
      <div className="workspace-switch"><span className="workspace-avatar">{initials(user.name)}</span><span className="workspace-copy"><strong>{user.name}</strong><small>Personal network</small></span><ChevronDown size={15} /></div>
      <nav className="primary-nav" aria-label="Main navigation">
        <span className="nav-caption">WORKSPACE</span>
        <button className={view === 'overview' ? 'nav-item active' : 'nav-item'} onClick={() => onNavigate('overview')}><Compass size={17} />Overview</button>
        <button className={view === 'network' ? 'nav-item active' : 'nav-item'} onClick={() => onNavigate('network')}><Network size={17} />Trust network<span className="nav-count">NEW</span></button>
        <span className="nav-caption nav-caption-spaced">YOUR CIRCLE</span>
        <button className="nav-item" onClick={() => onNavigate('overview')}><Heart size={17} />My vouches</button>
        <button className="nav-item" onClick={() => onNavigate('network')}><Users size={17} />Connections</button>
      </nav>
      <div className="sidebar-bottom">
        <div className="privacy-note"><ShieldCheck size={16} /><span>Your word stays<br />with your network.</span></div>
        <button className="nav-item logout-button" onClick={onLogout}><LogOut size={17} />Sign out</button>
        <div className="sidebar-version">VOUCH NETWORK <span>v1.0</span></div>
      </div>
    </aside>
  )
}

function Stars({ rating = 0, small = false }) {
  return <span className={small ? 'stars stars-small' : 'stars'} aria-label={`${rating} out of 5 stars`}>
    {[1, 2, 3, 4, 5].map((star) => <Star key={star} size={small ? 12 : 14} fill={star <= rating ? 'currentColor' : 'none'} />)}
  </span>
}

function App() {
  const [session, setSession] = useState(readSession)
  const [view, setView] = useState('overview')
  const [categories, setCategories] = useState([])
  const [providers, setProviders] = useState([])
  const [vouches, setVouches] = useState([])
  const [graph, setGraph] = useState({ nodes: [], edges: [] })
  const [category, setCategory] = useState('all')
  const [loading, setLoading] = useState(Boolean(session))
  const [dataError, setDataError] = useState('')
  const [modalVouch, setModalVouch] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [toast, setToast] = useState('')
  const [refreshCount, setRefreshCount] = useState(0)
  const [selectedNode, setSelectedNode] = useState('')
  const [algorithm, setAlgorithm] = useState('BFS')
  const [traversal, setTraversal] = useState(null)

  async function login(email, password) {
    const result = await api.login(email, password)
    saveAccessToken(result.access_token)
    localStorage.setItem(userStorageKey, JSON.stringify(result.user))
    setLoading(true)
    setSession({ token: result.access_token, user: result.user })
  }

  function logout() {
    saveAccessToken(null)
    localStorage.removeItem(userStorageKey)
    setSession(null)
    setVouches([])
    setGraph({ nodes: [], edges: [] })
  }

  useEffect(() => {
    if (!session) return undefined
    let cancelled = false
    Promise.all([
      api.categories(),
      api.providers(),
      api.vouches(session.user.id, category),
      api.graph(),
    ]).then(([nextCategories, nextProviders, nextVouches, nextGraph]) => {
      if (cancelled) return
      const providerCategory = new Map()
      for (const edge of nextGraph.edges || []) {
        if (edge.category !== 'friend' && !providerCategory.has(edge.target)) providerCategory.set(edge.target, edge.category)
      }
      const providerById = new Map(nextProviders.map((provider) => [provider.id, provider]))
      const nextNodes = (nextGraph.nodes || []).map((node) => ({
        ...node,
        type: providerById.has(node.id) || providerCategory.has(node.id) || node.type === 'provider' ? 'provider' : 'person',
        category: providerCategory.get(node.id) || providerById.get(node.id)?.category || node.category,
      }))
      setCategories(nextCategories)
      setProviders(nextProviders)
      setVouches(nextVouches)
      setGraph({ nodes: nextNodes, edges: nextGraph.edges || [] })
      setLoading(false)
    }).catch((error) => {
      if (cancelled) return
      setDataError(error.message || 'Unable to load your workspace.')
      setLoading(false)
    })
    return () => { cancelled = true }
  }, [session, category, refreshCount])

  function flash(message) {
    setToast(message)
    window.setTimeout(() => setToast(''), 2800)
  }

  async function saveVouch(payload) {
    if (modalVouch) await api.updateVouch(modalVouch.id, payload)
    else await api.createVouch(payload)
    setShowForm(false)
    setModalVouch(null)
    setLoading(true)
    setDataError('')
    setRefreshCount((count) => count + 1)
    flash(modalVouch ? 'Your vouch has been updated.' : 'Your vouch has been added.')
  }

  async function deleteVouch(vouch) {
    const name = providers.find((provider) => provider.id === vouch.to_provider_id)?.name || nameFromId(vouch.to_provider_id)
    if (!window.confirm(`Remove your vouch for ${name}?`)) return
    try {
      await api.deleteVouch(vouch.id)
      setLoading(true)
      setDataError('')
      setRefreshCount((count) => count + 1)
      setTraversal(null)
      flash('Vouch removed from your network.')
    } catch (error) {
      flash(error.message || 'Could not remove this vouch.')
    }
  }

  function openCreateForm() {
    setModalVouch(null)
    setShowForm(true)
  }

  function openEditForm(vouch) {
    const provider = providers.find((item) => item.id === vouch.to_provider_id)
    setModalVouch({ ...vouch, provider_name: provider?.name || nameFromId(vouch.to_provider_id) })
    setShowForm(true)
  }

  function runBfs() {
    const result = breadthFirstSearch(graph, session.user.id, category, selectedNode)
    const targetPathFound = !selectedNode || result.targetPath.length > 0
    const targetPath = targetPathFound ? result.targetPath : []
    const highlightedEdges = selectedNode
      ? result.targetPath.slice(1).map((id, index) => `${result.targetPath[index]}->${id}`)
      : []
    setTraversal({ mode: 'BFS', traversalOrder: result.order, edgeKeys: highlightedEdges, providers: result.providers, targetId: selectedNode, targetPath })
    flash(`Breadth-first search reached ${result.order.length} people and providers.`)
  }

  function runDfs() {
    if (!selectedNode) return
    const target = graph.nodes.find((node) => node.id === selectedNode)
    if (!target) {
      setTraversal(null)
      flash('Choose a destination in the current network.')
      return
    }
    const result = depthFirstSearch(graph, session.user.id, target.id, category)
    const targetPath = Array.isArray(result?.path)
      ? result.path
      : Array.isArray(result?.path?.nodes) ? result.path.nodes : []
    const edgeKeys = []
    for (let index = 0; index < targetPath.length - 1; index += 1) {
      const currentNode = targetPath[index]
      const nextNode = targetPath[index + 1]
      if (!currentNode || !nextNode) continue
      edgeKeys.push(`${currentNode}->${nextNode}`)
    }
    const found = Boolean(result?.found && targetPath.length)
    setTraversal({ mode: 'DFS', traversalOrder: result?.visited || [], edgeKeys, targetPath, found, cycleDetected: result?.cycleDetected })
    flash(found ? `Trust path found in ${Math.max(targetPath.length - 1, 0)} step${targetPath.length === 2 ? '' : 's'}.` : 'No trust path to that node in the selected category.')
  }

  if (!session) return <LoginScreen onLogin={login} />

  const visibleVouches = vouches
  const ratedVouches = visibleVouches.filter((vouch) => Number(vouch.rating) > 0)
  const averageRating = ratedVouches.length
    ? (ratedVouches.reduce((sum, vouch) => sum + Number(vouch.rating), 0) / ratedVouches.length).toFixed(1)
    : '—'
  const categoryCount = new Set(visibleVouches.map((vouch) => vouch.category).filter((item) => item !== 'friend')).size
  const filteredGraphEdges = category === 'all'
    ? graph.edges
    : graph.edges.filter((edge) => edge.category === category || edge.category === 'friend')
  const filteredGraphNodeIds = new Set(filteredGraphEdges.flatMap((edge) => [edge.source, edge.target]))
  const filteredGraphNodes = category === 'all'
    ? graph.nodes
    : graph.nodes.filter((node) => filteredGraphNodeIds.has(node.id) || node.id === session.user.id)
  const traversalPath = Array.isArray(traversal?.targetPath)
    ? traversal.targetPath
    : Array.isArray(traversal?.targetPath?.nodes) ? traversal.targetPath.nodes : []

  return (
    <div className="app-shell">
      <Sidebar view={view} onNavigate={(nextView) => { setView(nextView); setTraversal(null) }} user={session.user} onLogout={logout} />
      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{view === 'network' ? 'Trust network' : 'Overview'}</strong></div>
          <div className="topbar-actions"><span className="connection-status"><i />NETWORK LIVE</span><button className="icon-button topbar-help" title="Help and support"><CircleHelp size={17} /></button><button className="user-chip" title={`Signed in as ${session.user.email}`}><span className="user-avatar">{initials(session.user.name)}</span><span>{session.user.name}</span><ChevronDown size={14} /></button></div>
        </header>

        <div className="page-content">
          {dataError && <div className="error-banner" role="alert"><span>{dataError}</span><button className="icon-button" onClick={() => setRefreshCount((count) => count + 1)} title="Retry"><RefreshCw size={15} /></button></div>}
          {view === 'overview' ? (
            <>
              <section className="page-heading overview-heading">
                <div><span className="eyebrow">YOUR TRUST, IN MOTION</span><h1>Good people travel<br className="desktop-break" /> through good people.</h1><p>A living record of who you trust, and how far that trust can travel.</p></div>
                <div className="heading-actions"><button className="button button-quiet" onClick={() => setView('network')}><Network size={16} />Explore network</button><button className="button button-primary" onClick={openCreateForm}><Plus size={17} />Add a vouch</button></div>
              </section>

              <section className="metric-row" aria-label="Vouch summary">
                <article className="metric-card metric-highlight"><div className="metric-topline"><span>YOUR VOUCHES</span><Heart size={16} /></div><strong>{loading ? '—' : visibleVouches.length.toString().padStart(2, '0')}</strong><small>Recommendations you stand behind</small></article>
                <article className="metric-card"><div className="metric-topline"><span>AVERAGE RATING</span><Star size={16} /></div><strong>{loading ? '—' : averageRating}<span className="metric-unit">/ 5</span></strong><small>Across your recommendations</small></article>
                <article className="metric-card"><div className="metric-topline"><span>CATEGORIES</span><Compass size={16} /></div><strong>{loading ? '—' : categoryCount.toString().padStart(2, '0')}</strong><small>Parts of life covered</small></article>
                <article className="metric-card"><div className="metric-topline"><span>NETWORK NODES</span><Users size={16} /></div><strong>{loading ? '—' : graph.nodes.length.toString().padStart(2, '0')}</strong><small>People and providers connected</small></article>
              </section>

              <section className="ledger-section">
                <div className="section-heading"><div><span className="eyebrow">THE PEOPLE YOU TRUST</span><h2>Your vouches</h2></div><div className="ledger-tools"><label className="filter-select"><Search size={15} /><select aria-label="Filter vouches by category" onChange={(event) => setCategory(event.target.value)} value={category}><option value="all">All categories</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><ChevronDown size={14} /></label><button className="button button-outline" onClick={openCreateForm}><Plus size={15} />New vouch</button></div></div>
                <div className="ledger-table-wrap">
                  <table className="ledger-table">
                    <thead><tr><th>PROVIDER</th><th>CATEGORY</th><th>RATING</th><th>YOUR NOTE</th><th>DATE</th><th><span className="sr-only">Actions</span></th></tr></thead>
                    <tbody>
                      {loading ? <tr><td className="table-empty" colSpan="6"><span className="spinner spinner-dark" />Loading your vouches…</td></tr> : visibleVouches.length === 0 ? <tr><td className="table-empty" colSpan="6"><div className="empty-icon"><Heart size={20} /></div><strong>No vouches here yet</strong><span>Add a trusted provider to start a useful record.</span></td></tr> : visibleVouches.map((vouch) => {
                        const provider = providers.find((item) => item.id === vouch.to_provider_id)
                        const providerName = provider?.name || nameFromId(vouch.to_provider_id)
                        return <tr key={vouch.id}>
                          <td><div className="provider-cell"><span className="provider-avatar">{initials(providerName)}</span><span><strong>{providerName}</strong><small>{provider?.description || 'Recommended by you'}</small></span></div></td>
                          <td><span className={`category-pill category-${vouch.category}`}>{categoryTitle(vouch.category, categories)}</span></td>
                          <td><div className="rating-cell"><Stars rating={vouch.rating || 0} small /><span>{vouch.rating || '—'}</span></div></td>
                          <td className="note-cell">{vouch.message || <span className="muted-note">No note added</span>}</td>
                          <td className="date-cell">{formatDate(vouch.timestamp || vouch.created_at)}</td>
                          <td><div className="row-actions"><button className="icon-button" title="Edit vouch" aria-label={`Edit ${providerName} vouch`} onClick={() => openEditForm(vouch)}><span className="edit-glyph">✎</span></button><button className="icon-button danger-icon" title="Delete vouch" aria-label={`Delete ${providerName} vouch`} onClick={() => deleteVouch(vouch)}><X size={15} /></button></div></td>
                        </tr>
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="ledger-footer"><span>Showing {visibleVouches.length} {visibleVouches.length === 1 ? 'vouch' : 'vouches'}</span><button className="text-button" onClick={() => setView('network')}>See how trust travels <ArrowUpRight size={14} /></button></div>
              </section>

              <section className="network-teaser">
                <div className="teaser-icon"><Network size={21} /></div><div className="teaser-copy"><span className="eyebrow">BEYOND THE FIRST HANDSHAKE</span><h2>Follow a recommendation back to its source.</h2><p>See your trust network, find the closest route, and understand every connection along the way.</p></div><button className="button button-dark" onClick={() => setView('network')}>Open trust network <ArrowUpRight size={16} /></button>
                <div className="teaser-lines" aria-hidden="true"><span /><span /><span /><i /><i /></div>
              </section>
            </>
          ) : (
            <>
              <section className="page-heading graph-heading">
                <div><span className="eyebrow">THE PEOPLE BEHIND THE RECOMMENDATION</span><h1>Your trust network.</h1><p>Explore real connections, shortest routes, and the exact path behind a vouch.</p></div>
                <div className="heading-actions"><label className="filter-select graph-filter"><span className="filter-dot" /><select aria-label="Filter graph by category" onChange={(event) => { setCategory(event.target.value); setSelectedNode(''); setTraversal(null) }} value={category}><option value="all">Every category</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select><ChevronDown size={14} /></label><button className="button button-primary" onClick={openCreateForm}><Plus size={17} />Add a vouch</button></div>
              </section>

              <section className="graph-stats"><div><span>PEOPLE IN VIEW</span><strong>{filteredGraphNodes.length}</strong></div><div><span>TRUST LINKS</span><strong>{filteredGraphEdges.length}</strong></div><div><span>ACTIVE CATEGORY</span><strong>{category === 'all' ? 'All' : categoryTitle(category, categories)}</strong></div><div className="graph-status"><i />Live network data</div></section>

              <section className="network-workspace">
                <div className="network-visual-panel">
                  {loading ? <div className="graph-loading"><span className="spinner spinner-dark" />Refreshing network…</div> : <GraphErrorBoundary><NetworkGraph nodes={filteredGraphNodes} edges={filteredGraphEdges} providers={providers} rootId={session.user.id} category={category} activeEdgeKeys={traversal?.edgeKeys || []} targetPath={traversalPath} selectedNode={selectedNode} onSelectNode={setSelectedNode} /></GraphErrorBoundary>}
                </div>
                <aside className="graph-inspector">
                  <div className="inspector-head"><span className="eyebrow">NETWORK TOOLS</span><strong>Trace a connection</strong><p>Choose a traversal to understand how recommendations move through your circle.</p></div>
                  <div className="algorithm-toggle" role="group" aria-label="Graph traversal algorithm"><button aria-pressed={algorithm === 'BFS'} className={algorithm === 'BFS' ? 'algorithm-button active' : 'algorithm-button'} onClick={() => { setAlgorithm('BFS'); setTraversal(null) }}><GitBranch size={15} />BFS</button><button aria-pressed={algorithm === 'DFS'} className={algorithm === 'DFS' ? 'algorithm-button active' : 'algorithm-button'} onClick={() => { setAlgorithm('DFS'); setTraversal(null) }}><Compass size={15} />DFS</button></div>
                  <p className="algorithm-note"><strong>{algorithm === 'DFS' ? 'Depth-first search' : 'Breadth-first search'}</strong>{algorithm === 'DFS' ? ' follows one route deeply, then backtracks to trace a selected connection.' : ' explores nearby connections first, ranking providers by the shortest trust distance.'}</p>
                  <label className="field-label" htmlFor="target-node">{algorithm === 'DFS' ? 'Trace to a person or provider' : 'Target for shortest path (optional)'}</label>
                  <select id="target-node" className="target-select" onChange={(event) => setSelectedNode(event.target.value)} value={selectedNode}>
                    <option value="">Choose a node…</option>
                    {filteredGraphNodes.filter((node) => node.id !== session.user.id).map((node) => <option key={node.id} value={node.id}>{providers.find((provider) => provider.id === node.id)?.name || node.label || nameFromId(node.id)}</option>)}
                  </select>
                  <button className="button button-primary run-search" disabled={algorithm === 'DFS' && !selectedNode} onClick={algorithm === 'DFS' ? runDfs : runBfs}>
                    {algorithm === 'DFS' ? <Compass size={16} /> : <GitBranch size={16} />}{algorithm === 'DFS' ? 'Trace trust path' : 'Run breadth-first search'}
                  </button>
                  {traversal && <div className="traversal-results">
                    <div className="result-heading"><span>{traversal.mode === 'BFS' ? 'CLOSEST PROVIDERS' : 'TRUST PATH'}</span><button className="icon-button" title="Clear traversal" onClick={() => setTraversal(null)}><X size={14} /></button></div>
                    {traversal.mode === 'BFS' ? traversal.targetId ? traversalPath.length ? <div className="dfs-result"><span className="verified-path"><ShieldCheck size={16} /> SHORTEST TRUST PATH</span><div className="path-timeline">{traversalPath.map((id, index) => <div className="path-step" key={`${id}-${index}`}><span className={`path-marker${index === 0 ? ' path-origin' : index === traversalPath.length - 1 ? ' path-destination' : ''}`} />{index < traversalPath.length - 1 && <span className="path-connector" />}<strong>{id === session.user.id ? 'You' : providers.find((provider) => provider.id === id)?.name || nameFromId(id)}</strong><small>{index === 0 ? 'Starting point' : index === traversalPath.length - 1 ? 'Selected destination' : 'Connection'}</small></div>)}</div><span className="path-distance">{traversalPath.length - 1} {traversalPath.length === 2 ? 'degree' : 'degrees'} of trust</span></div> : <p className="no-results">No path connects to the selected node in this category.</p> : traversal.providers.length ? traversal.providers.map((result, index) => {
                      const providerName = providers.find((provider) => provider.id === result.id)?.name || nameFromId(result.id)
                      return <button className="path-result" key={result.id} onClick={() => setSelectedNode(result.id)}><span className="result-rank">{String(index + 1).padStart(2, '0')}</span><span><strong>{providerName}</strong><small>{result.distance} {result.distance === 1 ? 'step' : 'steps'} · {result.path.map((id) => id === session.user.id ? 'You' : providers.find((provider) => provider.id === id)?.name || nameFromId(id)).join(' → ')}</small></span><ArrowUpRight size={15} /></button>
                    }) : <p className="no-results">No providers are reachable in this category yet.</p> : traversal.found && traversalPath.length ? <div className="dfs-result"><span className="verified-path"><ShieldCheck size={16} /> VERIFIED TRUST PATH</span><div className="path-timeline">{traversalPath.map((id, index) => <div className="path-step" key={`${id}-${index}`}><span className={`path-marker${index === 0 ? ' path-origin' : index === traversalPath.length - 1 ? ' path-destination' : ''}`} />{index < traversalPath.length - 1 && <span className="path-connector" />}<strong>{id === session.user.id ? 'You' : providers.find((provider) => provider.id === id)?.name || nameFromId(id)}</strong><small>{index === 0 ? 'Starting point' : index === traversalPath.length - 1 ? 'Trusted destination' : 'Connection'}</small></div>)}</div><span className="path-distance">{traversalPath.length - 1} {traversalPath.length === 2 ? 'degree' : 'degrees'} of trust</span></div> : <p className="no-results">No path connects these nodes in the selected category.</p>}
                  </div>}
                  {!traversal && <div className="inspector-footnote"><ShieldCheck size={15} /><span>Paths are calculated from the current network edges and respect your category filter.</span></div>}
                </aside>
              </section>
              <section className="graph-explainer"><span className="explainer-mark">i</span><p><strong>How to read this map</strong> People are green, providers are blue, and your account is coral. Colored links show vouch categories. BFS ranks nearby options; DFS traces one exact route.</p><button className="text-button" onClick={() => setView('overview')}>Back to your vouches <ArrowDownRight size={14} /></button></section>
            </>
          )}
        </div>
      </main>

      {showForm && <VouchForm categories={categories} providers={providers} vouch={modalVouch} initialCategory={category === 'all' ? undefined : category} onClose={() => { setShowForm(false); setModalVouch(null) }} onSave={saveVouch} />}
      {toast && <div className="toast-message" role="status"><span className="toast-mark"><Heart size={14} fill="currentColor" /></span>{toast}<button className="toast-close" onClick={() => setToast('')} aria-label="Dismiss"><X size={14} /></button></div>}
    </div>
  )
}

export default App
