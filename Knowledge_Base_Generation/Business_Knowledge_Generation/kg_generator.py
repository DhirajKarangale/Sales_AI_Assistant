import json
import os

def generate_knowledge_graph(events: list[dict], base_dir: str):
    nodes = {}
    edges = []

    def add_node(id_val, label, properties=None):
        if not id_val:
            return
        if id_val not in nodes:
            nodes[id_val] = {"id": id_val, "label": label, "properties": properties or {}}
        else:
            if properties:
                nodes[id_val]["properties"].update(properties)

    def add_edge(source, target, relation):
        if not source or not target:
            return
        edge = {"source": source, "target": target, "relation": relation}
        if edge not in edges:
            edges.append(edge)

    for event in events:
        evt_id = event.get("source_id", "unknown_event")
        evt_type = event.get("event_type", "unknown")
        sp = event.get("salesperson")
        cust = event.get("customer")
        proj = event.get("project")
        participants = event.get("participants", [])

        add_node(evt_id, "Event", {"type": evt_type, "summary": event.get("summary")})

        if sp:
            add_node(sp, "Salesperson")
            add_edge(sp, evt_id, "PARTICIPATED_IN")
            if cust:
                add_edge(sp, cust, "MANAGES")
            if proj:
                add_edge(sp, proj, "OWNS")

        if cust:
            add_node(cust, "Customer")
            if proj:
                add_edge(cust, proj, "HAS_PROJECT")
            add_edge(cust, evt_id, "INVOLVED_IN")

        if proj:
            add_node(proj, "Project")
            add_edge(proj, evt_id, "HAS_EVENT")

        for p in participants:
            email = p.get("email")
            name = p.get("name")
            person_id = email if email else name
            if person_id:
                add_node(person_id, "Person", {"name": name, "email": email})
                add_edge(person_id, evt_id, "ATTENDED")
                if cust:
                    add_edge(person_id, cust, "BELONGS_TO")
                if proj:
                    add_edge(person_id, proj, "INVOLVED_IN")

    graph = {
        "nodes": list(nodes.values()),
        "edges": edges
    }

    kg_path = os.path.join(base_dir, "knowledge_graph.json")
    with open(kg_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)
    
    print(f"Knowledge graph generated with {len(nodes)} nodes and {len(edges)} edges at {kg_path}")
