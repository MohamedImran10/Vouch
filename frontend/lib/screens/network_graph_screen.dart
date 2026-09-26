import 'package:flutter/material.dart';
import 'package:graphview/GraphView.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

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

class _NetworkGraphScreenState extends State<NetworkGraphScreen> {
  final Graph graph = Graph()..isTree = false;
  BuchheimWalkerConfiguration builder = BuchheimWalkerConfiguration();

  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _configureGraph();
    _loadGraph();
  }

  void _configureGraph() {
    builder
      ..siblingSeparation = (100)
      ..levelSeparation = (150)
      ..subtreeSeparation = (150)
      ..orientation = (BuchheimWalkerConfiguration.ORIENTATION_TOP_BOTTOM);
  }

  Future<void> _loadGraph() async {
    try {
      final apiService = context.read<ApiService>();
      final graphData = await apiService.getFullGraph();

      _buildGraphFromData(graphData);

      setState(() => _isLoading = false);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  void _buildGraphFromData(Map<String, dynamic> data) {
    final nodes = data['nodes'] as Map<String, dynamic>;
    final nodeMap = <String, Node>{};

    // Create nodes
    for (final nodeId in nodes.keys) {
      final node = Node.Id(nodeId);
      nodeMap[nodeId] = node;
      graph.addNode(node);
    }

    // Create edges
    for (final entry in nodes.entries) {
      final fromId = entry.key;
      final edges = entry.value as List<dynamic>;

      for (final edge in edges) {
        final toId = edge['to'] as String;
        if (nodeMap.containsKey(toId)) {
          graph.addEdge(nodeMap[fromId]!, nodeMap[toId]!);
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trust Network Graph'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showLegend(),
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(Icons.error_outline, size: 64, color: Colors.red),
                        const SizedBox(height: 16),
                        Text('Error loading graph'),
                        const SizedBox(height: 8),
                        Text(_error!),
                        const SizedBox(height: 24),
                        ElevatedButton(
                          onPressed: _loadGraph,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : Column(
                  children: [
                    // Legend banner
                    Container(
                      padding: const EdgeInsets.all(12),
                      color: Theme.of(context).colorScheme.surfaceVariant,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          _buildLegendItem('You', Colors.blue),
                          _buildLegendItem('Friends', Colors.orange),
                          _buildLegendItem('Providers', Colors.green),
                        ],
                      ),
                    ),

                    // Graph view
                    Expanded(
                      child: InteractiveViewer(
                        constrained: false,
                        boundaryMargin: const EdgeInsets.all(100),
                        minScale: 0.1,
                        maxScale: 2.0,
                        child: GraphView(
                          graph: graph,
                          algorithm: BuchheimWalkerAlgorithm(
                            builder,
                            TreeEdgeRenderer(builder),
                          ),
                          paint: Paint()
                            ..color = Theme.of(context).colorScheme.primary
                            ..strokeWidth = 2
                            ..style = PaintingStyle.stroke,
                          builder: (Node node) {
                            final nodeId = node.key!.value as String;
                            return _buildNodeWidget(nodeId);
                          },
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  Widget _buildNodeWidget(String nodeId) {
    Color color;
    IconData icon;

    if (nodeId == widget.userId) {
      color = Colors.blue;
      icon = Icons.person;
    } else if (nodeId.contains('_')) {
      color = Colors.green;
      icon = Icons.business;
    } else {
      color = Colors.orange;
      icon = Icons.people;
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 2),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 4),
          Text(
            _formatNodeLabel(nodeId),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: color,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String label, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 16,
          height: 16,
          decoration: BoxDecoration(
            color: color.withOpacity(0.3),
            shape: BoxShape.circle,
            border: Border.all(color: color, width: 2),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }

  String _formatNodeLabel(String nodeId) {
    if (nodeId == widget.userId) return 'You';
    return nodeId.split('_')[0].replaceFirst(
          nodeId[0],
          nodeId[0].toUpperCase(),
        );
  }

  void _showLegend() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Graph Legend'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildLegendRow(Icons.person, 'Blue circles', 'You (starting point)', Colors.blue),
            const SizedBox(height: 12),
            _buildLegendRow(Icons.people, 'Orange circles', 'Your friends', Colors.orange),
            const SizedBox(height: 12),
            _buildLegendRow(Icons.business, 'Green circles', 'Service providers', Colors.green),
            const SizedBox(height: 16),
            const Text(
              'Pinch to zoom, drag to pan. Tap nodes for details.',
              style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  Widget _buildLegendRow(IconData icon, String title, String description, Color color) {
    return Row(
      children: [
        Icon(icon, color: color, size: 32),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
              Text(description, style: const TextStyle(fontSize: 12)),
            ],
          ),
        ),
      ],
    );
  }
}
