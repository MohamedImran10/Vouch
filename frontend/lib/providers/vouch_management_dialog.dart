import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart' hide Provider;

import '../models/models.dart';
import '../services/api_service.dart';

class VouchManagementDialog extends StatefulWidget {
  final String userId;
  final String categoryName;
  final String categoryId;
  final VoidCallback? onUpdated;

  const VouchManagementDialog({
    super.key,
    required this.userId,
    required this.categoryName,
    required this.categoryId,
    this.onUpdated,
  });

  @override
  State<VouchManagementDialog> createState() => _VouchManagementDialogState();
}

class _VouchManagementDialogState extends State<VouchManagementDialog> {
  final _formKey = GlobalKey<FormState>();
  final _ratingController = TextEditingController(text: '5');
  final _noteController = TextEditingController();
  List<Map<String, dynamic>> _vouches = [];
  List<Provider> _providers = [];
  bool _loading = true;
  bool _providersLoading = true;
  bool _saving = false;
  String? _error;
  String? _editingId;
  String? _selectedProviderId;

  @override
  void initState() {
    super.initState();
    _loadVouches();
    _loadProviders();
  }

  @override
  void dispose() {
    _ratingController.dispose();
    _noteController.dispose();
    super.dispose();
  }

  Future<void> _loadProviders() async {
    try {
      final providers = await context.read<ApiService>().getProviders(
        category: widget.categoryId,
      );
      if (!mounted) return;
      setState(() {
        _providers = providers;
        _providersLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _providersLoading = false);
    }
  }

  Future<void> _loadVouches() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final vouches = await context.read<ApiService>().getVouches(
        category: widget.categoryId,
        userId: widget.userId,
      );
      if (!mounted) return;
      setState(() {
        _vouches = vouches.where((vouch) {
          final category = vouch['category']?.toString().trim().toLowerCase();
          final owner = (vouch['from_user_id'] ?? vouch['from_user'])
              ?.toString();
          return category == widget.categoryId.trim().toLowerCase() &&
              owner == widget.userId;
        }).toList();
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _saveVouch() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _saving = true);
    try {
      final apiService = context.read<ApiService>();
      final wasEditing = _editingId != null;
      final payload = {
        'category': widget.categoryId,
        'message': _noteController.text.trim(),
        'rating': int.parse(_ratingController.text.trim()),
      };

      if (_editingId == null) {
        await apiService.createVouchCrud({
          ...payload,
          'to_provider_id': _selectedProviderId,
        });
      } else {
        await apiService.updateVouch(_editingId!, payload);
      }

      _clearForm();
      await _loadVouches();
      widget.onUpdated?.call();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(wasEditing ? 'Vouch updated' : 'Vouch created'),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Unable to save vouch: $e')));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _deleteVouch(String id) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete vouch?'),
        content: const Text('This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    try {
      await context.read<ApiService>().deleteVouch(id);
      await _loadVouches();
      widget.onUpdated?.call();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Unable to delete vouch: $e')));
      }
    }
  }

  void _editVouch(Map<String, dynamic> vouch) {
    final id = vouch['id']?.toString() ?? vouch['vouch_id']?.toString();
    if (id == null || id.isEmpty) return;
    setState(() {
      _editingId = id;
      _selectedProviderId = (vouch['to_provider_id'] ?? vouch['to_provider'])
          ?.toString();
      _ratingController.text = (vouch['rating'] ?? 5).toString();
      _noteController.text = (vouch['message'] ?? vouch['note'] ?? '')
          .toString();
    });
  }

  void _clearForm() {
    setState(() {
      _editingId = null;
      _selectedProviderId = null;
      _ratingController.text = '5';
      _noteController.clear();
    });
  }

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    return AlertDialog(
      title: Text('Vouches - ${widget.categoryName}'),
      content: SizedBox(
        width: math.min(520, size.width * 0.85),
        height: math.min(560, size.height * 0.75),
        child: Column(
          children: [
            Form(
              key: _formKey,
              child: Column(
                children: [
                  DropdownButtonFormField<String>(
                    key: ValueKey(_selectedProviderId),
                    initialValue: _selectedProviderId,
                    decoration: InputDecoration(
                      labelText: 'Provider',
                      helperText: _providersLoading
                          ? 'Loading providers...'
                          : _providers.isEmpty
                          ? 'No providers in this category'
                          : null,
                    ),
                    items: _providers
                        .map(
                          (provider) => DropdownMenuItem<String>(
                            value: provider.id,
                            child: Text(provider.name),
                          ),
                        )
                        .toList(),
                    onChanged: _saving || _editingId != null
                        ? null
                        : (providerId) =>
                              setState(() => _selectedProviderId = providerId),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return _providers.isEmpty
                            ? 'No providers are available in this category'
                            : 'Select a provider';
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _ratingController,
                    enabled: !_saving,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Rating (1-5)',
                    ),
                    validator: (value) {
                      final rating = int.tryParse(value?.trim() ?? '');
                      if (rating == null || rating < 1 || rating > 5) {
                        return 'Enter a rating from 1 to 5';
                      }
                      return null;
                    },
                  ),
                  TextFormField(
                    controller: _noteController,
                    enabled: !_saving,
                    maxLength: 500,
                    maxLines: 2,
                    decoration: const InputDecoration(labelText: 'Note'),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      FilledButton.icon(
                        onPressed: _saving ? null : _saveVouch,
                        icon: Icon(
                          _editingId == null ? Icons.thumb_up : Icons.save,
                          size: 18,
                        ),
                        label: Text(
                          _saving
                              ? 'Saving...'
                              : _editingId == null
                              ? 'Add vouch'
                              : 'Save changes',
                        ),
                      ),
                      const SizedBox(width: 8),
                      TextButton(
                        onPressed: _saving ? null : _clearForm,
                        child: const Text('Clear'),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Divider(),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : _error != null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text('Unable to load vouches: $_error'),
                          TextButton(
                            onPressed: _loadVouches,
                            child: const Text('Retry'),
                          ),
                        ],
                      ),
                    )
                  : _vouches.isEmpty
                  ? const Center(child: Text('No vouches yet'))
                  : ListView.builder(
                      itemCount: _vouches.length,
                      itemBuilder: (context, index) {
                        final vouch = _vouches[index];
                        final providerId =
                            (vouch['to_provider_id'] ??
                                    vouch['to_provider'] ??
                                    'Unknown provider')
                                .toString();
                        final message =
                            (vouch['message'] ?? vouch['note'] ?? '')
                                .toString();
                        final id =
                            vouch['id']?.toString() ??
                            vouch['vouch_id']?.toString();
                        return ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(providerId),
                          subtitle: Text(
                            [
                              if (vouch['rating'] != null)
                                'Rating: ${vouch['rating']}/5',
                              if (message.isNotEmpty) message,
                            ].join(' · '),
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(
                                tooltip: 'Edit vouch',
                                icon: const Icon(Icons.edit, size: 18),
                                onPressed: id == null
                                    ? null
                                    : () => _editVouch(vouch),
                              ),
                              IconButton(
                                tooltip: 'Delete vouch',
                                icon: const Icon(
                                  Icons.delete,
                                  size: 18,
                                  color: Colors.red,
                                ),
                                onPressed: id == null
                                    ? null
                                    : () => _deleteVouch(id),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Close'),
        ),
      ],
    );
  }
}
