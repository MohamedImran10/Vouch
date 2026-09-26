import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/models.dart';
import '../services/api_service.dart';

class TrustPathModal extends StatefulWidget {
  final String userId;
  final String providerId;
  final String providerName;

  const TrustPathModal({
    super.key,
    required this.userId,
    required this.providerId,
    required this.providerName,
  });

  @override
  State<TrustPathModal> createState() => _TrustPathModalState();
}

class _TrustPathModalState extends State<TrustPathModal> {
  TrustPath? _trustPath;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadTrustPath();
  }

  Future<void> _loadTrustPath() async {
    try {
      final apiService = context.read<ApiService>();
      final path = await apiService.getTrustPath(
        fromId: widget.userId,
        toId: widget.providerId,
      );

      setState(() {
        _trustPath = path;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.7,
      minChildSize: 0.5,
      maxChildSize: 0.9,
      expand: false,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Handle bar
              Container(
                margin: const EdgeInsets.symmetric(vertical: 12),
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Theme.of(context).dividerColor,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),

              // Header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  children: [
                    Icon(
                      Icons.account_tree,
                      color: Theme.of(context).colorScheme.primary,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Trust Path',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),

              const Divider(),

              // Content
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : _error != null
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Text(_error!),
                            ),
                          )
                        : _trustPath == null || !_trustPath!.valid
                            ? const Center(
                                child: Padding(
                                  padding: EdgeInsets.all(24),
                                  child: Text('No trust path found'),
                                ),
                              )
                            : ListView(
                                controller: scrollController,
                                padding: const EdgeInsets.all(20),
                                children: [
                                  // Provider info
                                  Card(
                                    color: Theme.of(context).colorScheme.primaryContainer,
                                    child: Padding(
                                      padding: const EdgeInsets.all(16),
                                      child: Column(
                                        children: [
                                          Text(
                                            widget.providerName,
                                            style: Theme.of(context)
                                                .textTheme
                                                .titleLarge
                                                ?.copyWith(
                                                  fontWeight: FontWeight.bold,
                                                  color: Theme.of(context)
                                                      .colorScheme
                                                      .onPrimaryContainer,
                                                ),
                                          ),
                                          const SizedBox(height: 8),
                                          Text(
                                            '${_trustPath!.path.length - 1} degree${_trustPath!.path.length > 2 ? 's' : ''} of separation',
                                            style: Theme.of(context)
                                                .textTheme
                                                .bodyMedium
                                                ?.copyWith(
                                                  color: Theme.of(context)
                                                      .colorScheme
                                                      .onPrimaryContainer,
                                                ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),

                                  const SizedBox(height: 24),

                                  // Path visualization
                                  ..._buildPathSteps(),
                                ],
                              ),
              ),
            ],
          ),
        );
      },
    );
  }

  List<Widget> _buildPathSteps() {
    if (_trustPath == null || _trustPath!.path.isEmpty) return [];

    final steps = <Widget>[];

    for (int i = 0; i < _trustPath!.path.length; i++) {
      final node = _trustPath!.path[i];
      final isFirst = i == 0;
      final isLast = i == _trustPath!.path.length - 1;

      // Node
      steps.add(_buildPathNode(node, isFirst, isLast));

      // Connector (except after last node)
      if (!isLast) {
        steps.add(_buildConnector());
      }
    }

    return steps;
  }

  Widget _buildPathNode(String node, bool isFirst, bool isLast) {
    Color color;
    IconData icon;
    String label;

    if (isFirst) {
      color = Colors.blue;
      icon = Icons.person;
      label = 'You';
    } else if (isLast) {
      color = Colors.green;
      icon = Icons.business;
      label = _formatNodeName(node);
    } else {
      color = Colors.orange;
      icon = Icons.people;
      label = _formatNodeName(node);
    }

    return Row(
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
            border: Border.all(color: color, width: 2),
          ),
          child: Icon(icon, color: color, size: 28),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    isFirst
                        ? 'Starting point'
                        : isLast
                            ? 'Service provider'
                            : 'Friend connection',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onSurfaceVariant,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildConnector() {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          const SizedBox(width: 27), // Center with icons
          Container(
            width: 2,
            height: 32,
            color: Theme.of(context).colorScheme.primary.withOpacity(0.3),
          ),
          const SizedBox(width: 15),
          Icon(
            Icons.arrow_downward,
            size: 20,
            color: Theme.of(context).colorScheme.primary,
          ),
          const SizedBox(width: 8),
          Text(
            'vouched for',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontStyle: FontStyle.italic,
                ),
          ),
        ],
      ),
    );
  }

  String _formatNodeName(String node) {
    return node
        .split('_')[0]
        .replaceFirst(node[0], node[0].toUpperCase());
  }
}
