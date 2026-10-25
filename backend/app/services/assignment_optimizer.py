"""Global shelter assignment on reachable cluster/shelter pairs.

Integer network simplex minimizes travel/depth cost with a dominating unmet-demand
penalty. Road throughput is a congestion estimate, not a hard fleet constraint.
"""
import networkx as nx


def optimize_assignments(demands, shelters, candidates):
    total = sum(int(d['unassigned']) for d in demands)
    if not total:
        return {}, {'algorithm': 'integer_min_cost_flow', 'objective_cost': 0}
    graph = nx.DiGraph()
    graph.add_node('sink', demand=total)
    graph.add_node('unserved', demand=0)
    graph.add_edge('unserved', 'sink', capacity=total, weight=0)
    max_cost = max((c['cost'] for options in candidates.values() for c in options), default=0)
    # One extra served person dominates the sum of all possible route costs.
    rescue_penalty = (total + 1) * (max_cost + 10001)
    for shelter_id, shelter in shelters.items():
        node = ('shelter', shelter_id)
        graph.add_node(node, demand=0)
        graph.add_edge(node, 'sink', capacity=0 if shelter['is_compromised'] else int(shelter['remaining_capacity']), weight=0)
    for demand in demands:
        cid = demand['cid']
        node = ('cluster', cid)
        graph.add_node(node, demand=-int(demand['unassigned']))
        priority = min(10000, max(0, round(demand['urgency_score'] * 100)))
        graph.add_edge(node, 'unserved', capacity=int(demand['unassigned']), weight=rescue_penalty + priority)
        for candidate in candidates[cid]:
            graph.add_edge(node, ('shelter', candidate['shelter_id']),
                           capacity=int(demand['unassigned']), weight=candidate['cost'])
    objective, flow = nx.network_simplex(graph)
    assignments = {(d['cid'], c['shelter_id']): flow[('cluster', d['cid'])].get(('shelter', c['shelter_id']), 0)
                   for d in demands for c in candidates[d['cid']]}
    return assignments, {'algorithm': 'integer_min_cost_flow', 'objective_cost': objective,
                         'unmet_penalty': rescue_penalty,
                         'objective': 'Maximize assigned demand, then minimize modeled travel/depth cost with urgency penalty for unmet demand.',
                         'limitations': 'Fixed candidate paths and shelter capacities; congestion is assessed after assignment, not jointly optimized.'}
