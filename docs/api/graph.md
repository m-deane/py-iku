# Graph

DAG (Directed Acyclic Graph) representation for flow analysis and validation.

---

## FlowGraph

Graph data structure representing the flow as a DAG with datasets and recipes as nodes.

```python
# Access via DataikuFlow
flow = convert(code)
graph = flow.graph  # FlowGraph instance
```

### Building the Graph

The graph is automatically built from `DataikuFlow` when you access `flow.graph`. It creates nodes for all datasets and recipes, and edges based on recipe inputs/outputs.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `nodes` | `List[FlowNode]` | All nodes |
| `dataset_nodes` | `List[FlowNode]` | Only dataset nodes |
| `recipe_nodes` | `List[FlowNode]` | Only recipe nodes |
| `edges` | `List[Tuple[str, str]]` | All edges as (source, target) pairs |

### Node Operations

```python
# Add nodes
node = graph.add_node("my_dataset", NodeType.DATASET, metadata={"type": "INPUT"})

# Add edges
graph.add_edge("input_data", "prepare_1")
graph.add_edge("prepare_1", "cleaned_data")

# Get node
node = graph.get_node("my_dataset")  # -> Optional[FlowNode]

# Get neighbors
graph.get_successors("my_dataset")    # -> List[str]
graph.get_predecessors("cleaned_data") # -> List[str]
```

### Graph Algorithms

#### Topological Sort

Returns nodes in dependency order (Kahn's algorithm).

```python
order = graph.topological_sort()
# ['input_data', 'prepare_1', 'cleaned_data', 'grouping_1', 'summary']
```

**Raises:** `ValueError` if the graph contains cycles.

#### Cycle Detection

Finds all cycles in the graph using DFS.

```python
cycles = graph.detect_cycles()
# [] if no cycles
# [['A', 'B', 'C', 'A']] if cycle exists
```

#### Disconnected Subgraphs

Finds groups of nodes that are not connected to each other.

```python
subgraphs = graph.find_disconnected_subgraphs()
# [['input1', 'prepare_1', 'output1'], ['input2', 'join_1', 'output2']]
```

#### Path Finding

Find a path between two nodes.

```python
path = graph.find_path("input_data", "summary")
# ['input_data', 'prepare_1', 'cleaned_data', 'grouping_1', 'summary']
# None if no path exists
```

#### Transitive Closure

Get all nodes reachable from a given node.

```python
reachable = graph.get_transitive_closure("input_data")
# {'prepare_1', 'cleaned_data', 'grouping_1', 'summary'}
```

---

## FlowNode

A node in the flow graph.

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | *required* | Node name |
| `node_type` | `NodeType` | *required* | DATASET or RECIPE |
| `metadata` | `Dict[str, Any]` | `{}` | Arbitrary metadata |

### Special Methods

```python
hash(node)         # Hashable by (name, node_type)
node1 == node2     # Equality by name and node_type
```

---

## NodeType

```python
from py2dataiku.models.flow_graph import NodeType
```

| Value | Description |
|-------|-------------|
| `DATASET` | Dataset node |
| `RECIPE` | Recipe node |

---

## Usage with DataikuFlow

The graph is most commonly accessed through `DataikuFlow`:

```python
flow = convert(code)

# Validate flow structure
result = flow.validate()
# Uses graph internally:
#   - Checks for cycles
#   - Checks for disconnected components
#   - Validates dataset references

# Get execution order
order = flow.graph.topological_sort()

# Check for cycles
cycles = flow.graph.detect_cycles()
if cycles:
    print(f"Warning: flow has cycles: {cycles}")

# Find independent subflows
subflows = flow.graph.find_disconnected_subgraphs()
print(f"Flow has {len(subflows)} independent pipeline(s)")
```
