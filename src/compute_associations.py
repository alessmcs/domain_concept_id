def get_bridging_associations(all_class_neighbors, impl_classes):
    """
    Given a graph of class associations and a set of implementation-detail classes,
    return the set of direct associations that should exist in the final domain model
    after impl classes are removed.

    For any path  D1 -> I1 -> ... -> In -> D2  (where all middle nodes are impl classes),
    we emit the pair (D1, D2).  Domain-to-domain edges that already exist are also kept.

    Only undirected pairs are returned (stored as frozensets to avoid duplicates).

    Args:
        all_class_neighbors (dict):
            { class_name: { "Association": [neighbor_name, ...], ... }, ... }
            As returned by xmiParser.extract_class_neighbors for every class.
        impl_classes (list | set):
            Class names that are classified as implementation detail.

    Returns:
        list[tuple[str, str]]: Sorted list of (classA, classB) pairs, both domain classes.

    Examples:
        D1 - I1 - I2 - D2          =>  (D1, D2)
        D1 - I1 - D2 - I2 - D3     =>  (D1, D2), (D2, D3)
        D1 - D2                     =>  (D1, D2)   [kept as-is]
    """
    impl_set = set(impl_classes)

    # Build an undirected adjacency set from all Association edges
    adjacency = {}  # { class_name: set(neighbors) }
    for cls, neighbors_by_type in all_class_neighbors.items():
        if cls not in adjacency:
            adjacency[cls] = set()
        for neighbor in neighbors_by_type.get("Association", []):
            adjacency[cls].add(neighbor)
            if neighbor not in adjacency:
                adjacency[neighbor] = set()
            adjacency[neighbor].add(cls)  # undirected

    domain_classes = set(adjacency.keys()) - impl_set
    bridging_pairs = set()

    # For each domain class, BFS that is allowed to *pass through* impl nodes
    # but stops (and records a pair) as soon as it reaches another domain node.
    # Each frontier entry is (node, frozenset_of_impl_nodes_on_path_so_far).
    for start in domain_classes:
        visited = {start}
        frontier = [(n, frozenset()) for n in adjacency.get(start, [])]
        visited.update(adjacency.get(start, []))

        while frontier:
            node, via = frontier.pop()
            if node not in impl_set:
                # Hit a domain node — record the pair, do NOT walk further from it
                pair = tuple(sorted([start, node]))
                if pair not in bridging_pairs:
                    bridging_pairs.add(pair)
                    if via:
                        print(f"[Bridge] {start} -- {node}  (via impl: {', '.join(sorted(via))})")
                    else:
                        print(f"[Bridge] {start} -- {node}  (direct association)")
            else:
                # Impl node — keep walking through it, accumulating it in the path
                for neighbor in adjacency.get(node, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        frontier.append((neighbor, via | {node}))

    return bridging_pairs


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    def make_neighbors(edges):
        """Helper: build all_class_neighbors from a list of undirected (A, B) edge tuples."""
        result = {}
        for a, b in edges:
            result.setdefault(a, {"Association": []})["Association"].append(b) or result[a]
            result.setdefault(b, {"Association": []})["Association"].append(a) or result[b]
            if "Association" not in result[a]: result[a]["Association"] = [b]
            if "Association" not in result[b]: result[b]["Association"] = [a]
        return result

    # --- Test 1: simple chain D1-I1-I2-D2 => (D1,D2) ---
    neighbors = make_neighbors([("D1","I1"), ("I1","I2"), ("I2","D2")])
    result = get_bridging_associations(neighbors, ["I1","I2"])
    assert result == [("D1","D2")], f"Test 1 failed: {result}"
    print("Test 1 passed:", result)

    # --- Test 2: D1-I1-D2-I2-D3 => (D1,D2), (D2,D3) ---
    neighbors = make_neighbors([("D1","I1"), ("I1","D2"), ("D2","I2"), ("I2","D3")])
    result = get_bridging_associations(neighbors, ["I1","I2"])
    assert set(result) == {("D1","D2"), ("D2","D3")}, f"Test 2 failed: {result}"
    print("Test 2 passed:", result)

    # --- Test 3: direct domain edge D1-D2 is preserved ---
    neighbors = make_neighbors([("D1","D2")])
    result = get_bridging_associations(neighbors, [])
    assert result == [("D1","D2")], f"Test 3 failed: {result}"
    print("Test 3 passed:", result)

    # --- Test 4: isolated impl class (no domain on either side) => nothing ---
    neighbors = make_neighbors([("I1","I2")])
    result = get_bridging_associations(neighbors, ["I1","I2"])
    assert result == [], f"Test 4 failed: {result}"
    print("Test 4 passed:", result)

    # --- Test 5: multiple impl nodes, two domain endpoints each side ---
    # D1-I1-I2-I3-D2 => (D1,D2)
    neighbors = make_neighbors([("D1","I1"),("I1","I2"),("I2","I3"),("I3","D2")])
    result = get_bridging_associations(neighbors, ["I1","I2","I3"])
    assert result == [("D1","D2")], f"Test 5 failed: {result}"
    print("Test 5 passed:", result)

    print("\nAll tests passed.")