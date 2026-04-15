#!/usr/bin/env python3
"""MCP Memory Server — Knowledge Graph."""

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Storage path
# ---------------------------------------------------------------------------
_DEFAULT_MEMORY_PATH = Path.home() / ".omni-lilith" / "memory" / "knowledge_graph.jsonl"


def _get_memory_path() -> Path:
    env = os.environ.get("MEMORY_FILE_PATH")
    if env:
        p = Path(env)
        return p if p.is_absolute() else Path(__file__).parent / p
    return _DEFAULT_MEMORY_PATH


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

def _load_graph(path: Path) -> dict:
    graph: dict = {"entities": [], "relations": []}
    if not path.exists():
        return graph
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        item = json.loads(line)
        if item.get("type") == "entity":
            graph["entities"].append({
                "name": item["name"],
                "entityType": item["entityType"],
                "observations": item["observations"],
            })
        elif item.get("type") == "relation":
            graph["relations"].append({
                "from": item["from"],
                "to": item["to"],
                "relationType": item["relationType"],
            })
    return graph


def _save_graph(path: Path, graph: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for e in graph["entities"]:
        lines.append(json.dumps({"type": "entity", "name": e["name"],
                                  "entityType": e["entityType"],
                                  "observations": e["observations"]}))
    for r in graph["relations"]:
        lines.append(json.dumps({"type": "relation", "from": r["from"],
                                  "to": r["to"],
                                  "relationType": r["relationType"]}))
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("memory-server")


@mcp.tool()
def create_entities(entities: list[dict]) -> list[dict]:
    """Create multiple new entities in the knowledge graph."""
    path = _get_memory_path()
    graph = _load_graph(path)
    existing = {e["name"] for e in graph["entities"]}
    new_entities = [e for e in entities if e["name"] not in existing]
    graph["entities"].extend(new_entities)
    _save_graph(path, graph)
    return new_entities


@mcp.tool()
def create_relations(relations: list[dict]) -> list[dict]:
    """Create multiple new relations between entities in the knowledge graph. Relations should be in active voice."""
    path = _get_memory_path()
    graph = _load_graph(path)

    def exists(r: dict) -> bool:
        return any(
            x["from"] == r["from"] and x["to"] == r["to"] and x["relationType"] == r["relationType"]
            for x in graph["relations"]
        )

    new_relations = [r for r in relations if not exists(r)]
    graph["relations"].extend(new_relations)
    _save_graph(path, graph)
    return new_relations


@mcp.tool()
def add_observations(observations: list[dict]) -> list[dict]:
    """Add new observations to existing entities in the knowledge graph.

    Each item: {"entityName": str, "contents": [str, ...]}
    """
    path = _get_memory_path()
    graph = _load_graph(path)
    results = []
    for o in observations:
        entity = next((e for e in graph["entities"] if e["name"] == o["entityName"]), None)
        if entity is None:
            raise ValueError(f"Entity '{o['entityName']}' not found")
        new_obs = [c for c in o["contents"] if c not in entity["observations"]]
        entity["observations"].extend(new_obs)
        results.append({"entityName": o["entityName"], "addedObservations": new_obs})
    _save_graph(path, graph)
    return results


@mcp.tool()
def delete_entities(entityNames: list[str]) -> str:
    """Delete multiple entities and their associated relations from the knowledge graph."""
    path = _get_memory_path()
    graph = _load_graph(path)
    graph["entities"] = [e for e in graph["entities"] if e["name"] not in entityNames]
    graph["relations"] = [
        r for r in graph["relations"]
        if r["from"] not in entityNames and r["to"] not in entityNames
    ]
    _save_graph(path, graph)
    return "Entities deleted successfully"


@mcp.tool()
def delete_observations(deletions: list[dict]) -> str:
    """Delete specific observations from entities in the knowledge graph.

    Each item: {"entityName": str, "observations": [str, ...]}
    """
    path = _get_memory_path()
    graph = _load_graph(path)
    for d in deletions:
        entity = next((e for e in graph["entities"] if e["name"] == d["entityName"]), None)
        if entity:
            entity["observations"] = [o for o in entity["observations"] if o not in d["observations"]]
    _save_graph(path, graph)
    return "Observations deleted successfully"


@mcp.tool()
def delete_relations(relations: list[dict]) -> str:
    """Delete multiple relations from the knowledge graph."""
    path = _get_memory_path()
    graph = _load_graph(path)

    def matches(r: dict) -> bool:
        return any(
            r["from"] == d["from"] and r["to"] == d["to"] and r["relationType"] == d["relationType"]
            for d in relations
        )

    graph["relations"] = [r for r in graph["relations"] if not matches(r)]
    _save_graph(path, graph)
    return "Relations deleted successfully"


@mcp.tool()
def read_graph() -> dict:
    """Read the entire knowledge graph."""
    return _load_graph(_get_memory_path())


@mcp.tool()
def search_nodes(query: str) -> dict:
    """Search for nodes in the knowledge graph based on a query."""
    graph = _load_graph(_get_memory_path())
    q = query.lower()
    filtered_entities = [
        e for e in graph["entities"]
        if q in e["name"].lower()
        or q in e["entityType"].lower()
        or any(q in o.lower() for o in e["observations"])
    ]
    names = {e["name"] for e in filtered_entities}
    filtered_relations = [
        r for r in graph["relations"]
        if r["from"] in names or r["to"] in names
    ]
    return {"entities": filtered_entities, "relations": filtered_relations}


@mcp.tool()
def open_nodes(names: list[str]) -> dict:
    """Open specific nodes in the knowledge graph by their names."""
    graph = _load_graph(_get_memory_path())
    name_set = set(names)
    filtered_entities = [e for e in graph["entities"] if e["name"] in name_set]
    filtered_names = {e["name"] for e in filtered_entities}
    filtered_relations = [
        r for r in graph["relations"]
        if r["from"] in filtered_names or r["to"] in filtered_names
    ]
    return {"entities": filtered_entities, "relations": filtered_relations}


if __name__ == "__main__":
    mcp.run()
