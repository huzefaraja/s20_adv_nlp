import re

import spacy
from spacy.tokens import Span, Doc

nlp = spacy.load("en_core_web_lg")
RE_QUOTE = re.compile(r"\"[^\"]*?\".*?[.!?,]", flags=re.S)
Doc.set_extension("quote", default=False, force=True)
Span.set_extension("quote", default=False, force=True)


def clean_entity(text):
    return re.sub('[^a-zA-Z .,]', '', text)


def get_longer_version(entities, entity):
    return max(entities[entity], key=len)


def resolve_entity(entities, entity):
    if entity not in entities:
        entities[entity] = set()
    for _entity in entities:
        if entity in _entity:
            entities[entity] = entities[_entity]
            entities[entity].add(_entity)
        if _entity in entity:
            entities[_entity].add(entity)
            entities[entity] = entities[_entity]
    return get_longer_version(entities, entity)


def from_doc(document):
    daq = {}
    entities = {}
    just_quotes = {}
    saved_quotes = []
    _docs = {}
    problems = {}
    doc_id = document.doc_id
    _docs[doc_id] = document.body
    try:
        doc = nlp(document.body)
        for match in RE_QUOTE.finditer(doc.text):
            start, end = match.span()
            span = doc.char_span(start, end)
            if span is not None:
                _doc = span.as_doc()
                i = 0
                for token in _doc[1:]:
                    i += 1
                    if token.is_quote:
                        break
                quote = _doc[1:i].as_doc()
                quote._.quote = True
                suffix = _doc[i + 1:].as_doc()
                people = []
                for ent in suffix.ents:
                    if ent.label_ == "PERSON":
                        entity = clean_entity(ent.text)
                        entity = resolve_entity(entities, entity)
                        people.append(entity)

                if len(people) == 1:
                    if doc_id not in daq:
                        daq[doc_id] = {}
                    if entity not in daq[doc_id]:
                        daq[doc_id][entity] = []
                    daq[doc_id][entity].append({'quote': quote.text, 'original_text': _doc.text})
                    if quote.text not in just_quotes:
                        just_quotes[quote.text] = []
                    else:
                        saved_quotes.append(quote.text)
                    just_quotes[quote.text].append({'doc_id': doc_id, 'original_text': _doc.text})
    except Exception as e:
        problems[doc_id] = e
    if doc_id in daq:
        return daq[doc_id]
