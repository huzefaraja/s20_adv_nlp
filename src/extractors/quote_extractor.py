import re
from pprint import pprint

import spacy
from data_sources import *
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_lg")
docs = session.query(ReutersDoc)

total_docs = docs.count()
num_docs = total_docs

pattern_quote = [{"IS_QUOTE": True}, {"OP": "*"}, {"IS_QUOTE": False}, {"OP": "*"}, {"IS_QUOTE": True}]
matcher_quote = Matcher(nlp.vocab)
matcher_quote.add("quote", None, pattern_quote)


def get_single_line_quote(doc):
    quote_count = 0
    for token in doc:
        if token.is_quote:
            quote_count += 1
            if quote_count > 2:
                return None
    return doc


def get_quote_prefix(doc, current):
    current -= 1
    if current < 0 or doc[current].text.strip() == "." and doc[current].text.strip() == "\"":
        return None
    while current > 0 and doc[current].text.strip() != "." and doc[current].text.strip() != "\"":
        current -= 1
    while doc[current].text.strip() in ['.', '']:
        current += 1
    return current


def get_quote_suffix(doc, current):
    current += 1
    if current >= len(doc) or doc[current].text.strip() == "." and doc[current].text.strip() == "\"":
        return None
    while current < len(doc) and doc[current].text.strip() != "." and doc[current].text.strip() != "\"":
        current += 1
    while current < len(doc) and doc[current].text.strip() in ['.', '']:
        current += 1
    return current + 1


class Quote:
    def __init__(self, doc, quote, start, end, prefix, suffix):
        self.doc = doc
        self.quote = quote
        self.start = start
        self.end = end
        self.prefix = prefix if prefix is not None else start
        self.suffix = suffix if suffix is not None else end
        self.quote_str = re.sub(r"\n", r" ", self._get_quote_str())
        self.quote_str = re.sub(r"\s+", r" ", self.quote_str)

    def _get_quote_str(self):
        quote = self.doc[self.prefix:self.suffix]
        return quote.text

    def __repr__(self):
        return str(self.quote_str)


def extract_entity(quote, token_index):
    entity_start_index = token_index
    entity_end_index = token_index + 1
    while quote.doc[entity_end_index].ent_type_ == "PERSON":
        token_index += 1
        entity_end_index += 1
    entity = quote.doc[entity_start_index: entity_end_index].text
    entity = re.sub("[\n,]", " ", entity)
    entity = re.sub("\s+", " ", entity).strip()
    return entity, token_index


def try_match(pattern, quote, out_entity, verbose=False):
    token_index = quote.prefix
    pattern_index = 1
    for _ in quote.doc[quote.prefix: quote.suffix]:
        if pattern_index < len(pattern):
            if token_index >= quote.suffix - 1: return False
            if verbose:
                print("Matching {} with {}".format(pattern[pattern_index], quote.doc[token_index]))
            if pattern[pattern_index] == "QUOTE":
                if quote.doc[token_index].text == "\"" and token_index != quote.end - 1:
                    token_index = quote.end - 1
            elif pattern[pattern_index] == "SPEAKER":
                if quote.doc[token_index].ent_type == 0:
                    if verbose:
                        print(quote.doc[token_index], "is not a person")
                    return False
                else:
                    entity, token_index = extract_entity(quote, token_index)
                    out_entity.append(entity)
            elif pattern[pattern_index] == "END":
                if verbose:
                    print("Matched end of quote")
                return True
            else:
                if token_index >= quote.suffix - 1 or pattern[pattern_index] != quote.doc[token_index].text:
                    if verbose:
                        print("Failed matching {} with {}".format(pattern[pattern_index], quote.doc[token_index]))
                    return False
                else:
                    if verbose:
                        print("Matched!")
        token_index += 1
        while token_index < quote.suffix - 1 and not quote.doc[token_index].is_alpha:
            token_index += 1
        pattern_index += 1
    return True


def add_pattern_hit(pattern_hits, pattern, quote, entity):
    pattern = " ".join(pattern)
    if pattern not in pattern_hits:
        pattern_hits[pattern] = []
    hit = {
        "quote": quote.quote,
        "speaker": entity
    }
    pattern_hits[pattern].append(hit)
    return hit


# Start here

num_docs = 1000
quotes = []
for document in docs[:num_docs]:
    doc_id = document.doc_id
    doc = nlp(document.body)
    matches = matcher_quote(doc)
    odd = True
    for match_id, start, end in matches:
        quote = get_single_line_quote(doc[start:end])
        if quote is not None:
            if odd:
                quotes.append(Quote(doc, quote, start, end, get_quote_prefix(doc, start), get_quote_suffix(doc, end)))
            odd = not odd

patterns = [
    ["START", "QUOTE", "said", "SPEAKER", "END"],
    ["START", "QUOTE", "announced", "SPEAKER", "END"],
    ["START", "QUOTE", "SPEAKER", "said", "END"]
]

pattern_hits = {}
verbose = True
for quote in quotes:
    if verbose:
        print(quote)
    for pattern in patterns:
        ents = []
        matches = try_match(pattern, quote, ents, verbose)
        if matches:
            if verbose:
                print()
                print("=" * 80)
                print("Matched Pattern: ", " ".join(pattern))
            hit = add_pattern_hit(pattern_hits, pattern, quote, ents[0])
            if verbose:
                print(hit)
                print("=" * 80)
                print()

    if verbose:
        print("_" * 80)
        print()

pprint(pattern_hits)
session.close()
