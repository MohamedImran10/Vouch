import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

/// Color palette per the visual specifications
class GraphColors {
  static const Color rootNode = Color(0xFF3B82F6);        // Electric Blue - "You"
  static const Color firstDegree = Color(0xFF10B981);    // Emerald Green - 1st Degree
  static const Color secondDegree = Color(0xFFF59E0B);   // Amber Yellow - 2nd Degree
  static const Color providerColor = Color(0xFF8B5CF6);   // Purple - Service Provider
  static const Color activeSelection = Color(0xFF06B6D4); // Neon Turquoise - Active Focus
  static const Color dimmedNode = Color(0xFF334155);      // Dark Slate Gray
  static const Color activeEdge = Color(0xFF22D3EE);      // Bright Cyan - Traversal Path
  static const Color inactiveEdge = Color(0xFF475569);    // Subtle Translucent Gray
}

/// Node degree categories
enum NodeDegree { zero, first, second, provider, other }

/// Represents a node in the graph with its metadata
@immutable
class NodeData {
  final String id;
  final String label;
  final NodeDegree degree;
  final Color baseColor;
  final bool isProvider;

  NodeData({
    required this.id,
    required this.label,
    required this.degree,
    required this.baseColor,
    required this.isProvider,
  });

  Color getColor({
    String? selectedNodeId,
    Set<String> highlightedNodeIds = const {},
    List<String> activePathNodeIds = const [],
  }) {
    // Active path takes precedence
    if (activePathNodeIds.contains(id)) {
      return GraphColors.activeSelection;
    }
    // Selected/focused node
    if (selectedNodeId == id) {
      return GraphColors.activeSelection;
    }
    // Dimmed node (not in highlighted set when something is selected)
    if (selectedNodeId != null && !highlightedNodeIds.contains(id)) {
      return GraphColors.dimmedNode.withOpacity(0.3);
    }
    // Base color by degree
    switch (degree) {
      case NodeDegree.zero:
        return baseColor; // You - Electric Blue
      case NodeDegree.first:
        return GraphColors.firstDegree; // 1st Degree - Emerald Green
      case NodeDegree.second:
        return GraphColors.secondDegree; // 2nd Degree - Amber Yellow
      case NodeDegree.provider:
        return GraphColors.providerColor; // Service Provider - Purple
      default:
        return baseColor;
    }
  }
}

/// Edge data for traversal paths
@immutable
class EdgeData {
  final String source;
  final String target;
  final double weight;
  final String category;
  bool isActivePath;
  bool isHighlighted;

  EdgeData({
    required this.source,
    required this.target,
    required this.weight,
    required this.category,
    this.isActivePath = false,
    this.isHighlighted = false,
  });
}

class NetworkGraphScreen extends StatefulWidget {
  final String userId;
  final String? highlightCategory;

  const NetworkGraphScreen({
    super.key,
    required this.userId,
    this.highlightCategory,
  });

  @override
  State<NetworkGraphScreen> createState() => _NetworkGraphScreenState();
}

class _NetworkGraphScreenState extends State<NetworkGraphScreen>
    with SingleTickerProviderStateMixin {
  bool _isLoading = true;
  String? _error;

  // Interactive state
  String? _selectedNodeId;
  final Set<String> _highlightedNodeIds = {};
  final List<String> _activePathNodeIds = [];
  double _zoom = 1.0;
  Offset _dragStart = Offset.zero;
  Offset _dragOffset = Offset.zero;

  // Animation
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  // Cached graph data from backend
  List<dynamic> _rawNodes = [];
  List<dynamic> _rawEdges = [];
  Map<String, NodeData> _nodeMap = {};
  List<EdgeData> _edgeList = [];

  // BFS/DFS traversal animation
  int _animationStep = 0;
  Timer? _traversalTimer;
  List<String> _traversalSequence = [];

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(_pulseController);
    _loadGraph();
  }

  @override
  void dispose() {
    _traversalTimer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _loadGraph() async {
    try {
      final apiService = context.read<ApiService>();
      final graphData = await apiService.getFullGraph();
      _rawNodes = (graphData['nodes'] ?? []) as List<dynamic>;
      _rawEdges = (graphData['edges'] ?? []) as List<dynamic>;
      _buildNodeData();
      _buildEdgeData();
      setState(() => _isLoading = false);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Error loading graph')),
      );
    }
  }

  void _buildNodeData() {
    _nodeMap.clear();
    for (final node in _rawNodes) {
      final id = node['id'] as String;
      final label = node['label'] as String;
      final type = node['type'] as String;
      final degree = (node['degree'] ?? 0) as int;
      NodeDegree nd;
      if (id == widget.userId) nd = NodeDegree.zero;
      else if (degree == 0) nd = NodeDegree.zero;
      else if (degree == 1) nd = NodeDegree.first;
      else if (degree == 2) nd = NodeDegree.second;
      else if (type == 'provider' || id.contains('_')) nd = NodeDegree.provider;
      else nd = NodeDegree.other;
      final isProvider = nd == NodeDegree.provider || id.contains('_');
      Color base;
      if (nd == NodeDegree.zero) base = GraphColors.rootNode;
      else if (nd == NodeDegree.first) base = GraphColors.firstDegree;
      else if (nd == NodeDegree.second) base = GraphColors.secondDegree;
      else if (nd == NodeDegree.provider) base = GraphColors.providerColor;
      else base = GraphColors.dimmedNode;
      _nodeMap[id] = NodeData(
        id: id,
        label: label,
        degree: nd,
        baseColor: base,
        isProvider: isProvider,
      );
    }
  }

  void _buildEdgeData() {
    _edgeList = [];
    for (final edge in _rawEdges) {
      _edgeList.add(EdgeData(
        source: edge['source'] as String,
        target: edge['target'] as String,
        weight: (edge['weight'] ?? 1).toDouble(),
        category: (edge['category'] ?? '') as String,
        isActivePath: false,
        isHighlighted: false,
      ));
    }
  }

  /// BFS/DFS traversal animation — highlights exact path edges sequentially
  void _startTraversalAnimation(List<String> pathNodeIds) {
    _traversalSequence = pathNodeIds;
    _animationStep = 0;
    _traversalTimer?.cancel();
    setState(() {
      _activePathNodeIds.clear();
      for (final e in _edgeList) {
        e.isActivePath = false;
        e.isHighlighted = false;
      }
    });
    _traversalTimer = Timer.periodic(const Duration(milliseconds: 600), (timer) {
      if (_animationStep >= _traversalSequence.length) {
        timer.cancel();
        return;
      }
      setState(() {
        _activePathNodeIds.add(_traversalSequence[_animationStep]);
        // Highlight edges between consecutive nodes in path
        for (final e in _edgeList) {
          e.isActivePath = false;
          for (int i = 0; i < _animationStep; i++) {
            if ((e.source == _traversalSequence[i] && e.target == _traversalSequence[i + 1]) ||
                (e.source == _traversalSequence[i + 1] && e.target == _traversalSequence[i])) {
              e.isActivePath = true;
            }
          }
        }
      });
      _animationStep++;
    });
  }

  /// Handle node tap — focus with color coding
  void _onNodeTap(String nodeId) {
    setState(() {
      if (_selectedNodeId == nodeId) {
        _selectedNodeId = null;
        _highlightedNodeIds.clear();
        _activePathNodeIds.clear();
        for (final e in _edgeList) { e.isActivePath = false; e.isHighlighted = false; }
      } else {
        _selectedNodeId = nodeId;
        _highlightedNodeIds.clear();
        // Highlight 1st-degree neighbors from adjacency
        for (final e in _edgeList) {
          if (e.source == nodeId || e.target == nodeId) {
            _highlightedNodeIds.add(e.source);
            _highlightedNodeIds.add(e.target);
          }
        }
        _highlightedNodeIds.add(nodeId);
      }
    });
  }

  /// Handle provider node tap — execute BFS/DFS traversal animation
  void _onProviderTap(String providerId) async {
    try {
      final apiService = context.read<ApiService>();
      final result = await apiService.getTrustPath(fromId: widget.userId, toId: providerId);
      if (result.valid && result.path.isNotEmpty) {
        final path = result.path;
        setState(() {
          _selectedNodeId = providerId;
          _highlightedNodeIds.clear();
          for (final p in path) _highlightedNodeIds.add(p);
        });
        _startTraversalAnimation(path);
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Path trace error: $e')));
    }
  }

  /// Reset view
  void _resetView() {
    _traversalTimer?.cancel();
    setState(() {
      _selectedNodeId = null;
      _highlightedNodeIds.clear();
      _activePathNodeIds.clear();
      for (final e in _edgeList) { e.isActivePath = false; e.isHighlighted = false; }
    });
  }

  /// Build legend banner
  Widget _buildLegend() {
    return Container(
      padding: const EdgeInsets.all(8),
      color: Theme.of(context).colorScheme.surfaceVariant,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _legendItem(color: GraphColors.rootNode, label: 'You', description: 'Electric Blue\nRoot User', icon: Icons.person),
          _legendItem(color: GraphColors.firstDegree, label: '1st Degree', description: 'Emerald Green\nDirect friends', icon: Icons.people),
          _legendItem(color: GraphColors.secondDegree, label: '2nd Degree', description: 'Amber Yellow\nFriends of friends', icon: Icons.hub),
          _legendItem(color: GraphColors.providerColor, label: 'Providers', description: 'Purple\nService Providers', icon: Icons.store),
        ],
      ),
    );
  }

  _legendItem({
    required Color color,
    required String label,
    required String description,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      color: color.withOpacity(0.1),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: color),
          const SizedBox(width: 4),
          Expanded(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold)),
                Text(description, style: const TextStyle(color: Colors.white70, fontSize: 9)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_error != null) return Scaffold(body: Center(child: Text('Error: $_error')));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Network Graph'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadGraph),
          IconButton(icon: const Icon(Icons.zoom_out_map), onPressed: _resetView),
        ],
      ),
      body: Column(
        children: [
          _buildLegend(),
          Expanded(
            child: InteractiveViewer(
              panEnabled: true,
              boundaryMargin: const EdgeInsets.all(20),
              minScale: 0.5,
              maxScale: 3.0,
              child: Container(
                color: Colors.black12,
                child: CustomPaint(
                  size: Size.infinite,
                  painter: _GraphPainter(
                    nodes: _nodeMap,
                    edges: _edgeList,
                    selectedNodeId: _selectedNodeId,
                    highlightedNodeIds: _highlightedNodeIds,
                    activePathNodeIds: _activePathNodeIds,
                    onNodeTap: _onNodeTap,
                    onProviderTap: _onProviderTap,
                  ),
                ),
              ),
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            color: Colors.black87,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Zoom: ${_zoom.toStringAsFixed(2)}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
                ElevatedButton(
                  onPressed: () {
                    final List<String> path = _activePathNodeIds.isNotEmpty ? _activePathNodeIds : [];
                    if (path.isNotEmpty) _startTraversalAnimation(path);
                  },
                  child: const Icon(Icons.play_arrow, size: 18),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// Custom painter for the 2D interactive graph canvas
class _GraphPainter extends CustomPainter {
  final Map<String, NodeData> nodes;
  final List<EdgeData> edges;
  final String? selectedNodeId;
  final Set<String> highlightedNodeIds;
  final List<String> activePathNodeIds;
  final Function(String) onNodeTap;
  final Function(String) onProviderTap;

  _GraphPainter({
    required this.nodes,
    required this.edges,
    required this.selectedNodeId,
    required this.highlightedNodeIds,
    required this.activePathNodeIds,
    required this.onNodeTap,
    required this.onProviderTap,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final centerX = size.width / 2;
    final centerY = size.height / 2;
    // Simple radial layout for demonstration
    final nodeIds = nodes.keys.toList();
    final radius = min(size.width, size.height) * 0.35;
    final positions = <String, Offset>{};
    for (int i = 0; i < nodeIds.length; i++) {
      final angle = 2 * pi * i / nodeIds.length;
      positions[nodeIds[i]] = Offset(centerX + radius * cos(angle), centerY + radius * sin(angle));
    }
    // Draw edges
    final paintEdge = Paint()..strokeWidth = 2;
    for (final e in edges) {
      final s = positions[e.source];
      final t = positions[e.target];
      if (s == null || t == null) continue;
      if (e.isActivePath) {
        paintEdge.color = GraphColors.activeEdge;
        paintEdge.strokeWidth = 3.5;
      } else if (e.isHighlighted || highlightedNodeIds.contains(e.source) || highlightedNodeIds.contains(e.target)) {
        paintEdge.color = Colors.white.withOpacity(0.5);
        paintEdge.strokeWidth = 2;
      } else {
        paintEdge.color = GraphColors.inactiveEdge.withOpacity(0.4);
        paintEdge.strokeWidth = 1;
      }
      canvas.drawLine(s, t, paintEdge);
    }
    // Draw nodes
    for (final entry in nodes.entries) {
      final id = entry.key;
      final data = entry.value;
      final pos = positions[id];
      if (pos == null) continue;
      final color = data.getColor(
        selectedNodeId: selectedNodeId,
        highlightedNodeIds: highlightedNodeIds,
        activePathNodeIds: activePathNodeIds,
      );
      final isSelected = selectedNodeId == id || activePathNodeIds.contains(id);
      final radius = isSelected ? 18.0 : 14.0;
      // Shadow
      final shadowPaint = Paint()..color = Colors.black.withOpacity(0.3)..maskFilter = const MaskFilter.blur(BlurStyle.normal, 4);
      canvas.drawCircle(pos, radius + 2, shadowPaint);
      // Fill
      final fillPaint = Paint()..color = isSelected ? color.withOpacity(0.95) : color.withOpacity(0.85)..style = PaintingStyle.fill;
      canvas.drawCircle(pos, radius, fillPaint);
      // Border
      final borderPaint = Paint()..color = isSelected ? GraphColors.activeSelection : Colors.white.withOpacity(0.7)..style = PaintingStyle.stroke..strokeWidth = 2;
      canvas.drawCircle(pos, radius, borderPaint);
      // Label
      final textStyle = TextStyle(color: Colors.white, fontSize: isSelected ? 10 : 8, fontWeight: FontWeight.bold);
      final textPainter = TextPainter(text: TextSpan(text: data.label, style: textStyle), textDirection: TextDirection.ltr, textAlign: TextAlign.center);
      textPainter.layout(minWidth: 0, maxWidth: 60);
      textPainter.paint(canvas, pos.translate(-textPainter.width / 2, radius + 4));
    }
  }

  @override
  bool shouldRepaint(covariant _GraphPainter old) => true;
}