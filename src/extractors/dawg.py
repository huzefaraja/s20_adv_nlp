from extractors.quote_extractor import QuoteExtractor, nlp
from graphviz import Digraph

extractor = QuoteExtractor(nlp, input_patterns='bootstrapped.json')

# to get the file `quotes.json`,
# please run the function run_on_docs (uncomment lines at the bottom of quote_extractor.py) with save=True
quotes, pattern_hits = (extractor.run_on_file("quotes.json", get_pattern_hits=True, bootstrap=True, save=True))

# pprint(pattern_hits)
# extractor.save_patterns("bootstrapped.json")


dot = Digraph(comment='DAWG')
nodes = {"START": {"distance_from_start": 0}, "END": {"distance_from_end": 0}}
dot.node("START")
dot.node("END")
edges = set()
for pattern in extractor.SEED_PATTERNS:
    if len(pattern_hits[pattern["readable_str"]]) < 5: continue
    print(pattern["readable_str"], "=>", len(pattern_hits[pattern["readable_str"]]))
    start = "START"

    d_start = 0
    for node in pattern["readable"][1:-1]:
        d_start += 1
        d_end = len(pattern["readable"]) - d_start
        d_speaker = pattern["readable"].index(node) - pattern["readable"].index("SPEAKER")
        d_quote = pattern["readable"].index(node) - pattern["readable"].index("QUOTE")
        if node not in nodes:
            nodes[node] = {
                "distance_from_start": d_start,
                "distance_from_end": d_end,
                "distance_from_speaker": d_speaker,
                "distance_from_quote": d_quote,
            }
        else:
            if (nodes[node]["distance_from_start"] != d_start and nodes[node]["distance_from_end"] != d_end) or (
                    nodes[node]["distance_from_speaker"] != d_speaker and
                    nodes[node]["distance_from_quote"] != d_quote):
                node = node + "_"
                nodes[node] = {
                    "distance_from_start": d_start,
                    "distance_from_end": d_end,
                    "distance_from_speaker": d_speaker,
                    "distance_from_quote": d_quote,
                }

        end = node
        if (start, end) not in edges:
            edges.add((start, end))
            dot.edge(start, end)
        start = node
    end = "END"
    if (start, end) not in edges:
        edges.add((start, end))
        dot.edge(start, end)
dot.view()
