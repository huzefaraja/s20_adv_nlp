import json
import re

import spacy
from data_sources import *
from spacy.matcher import Matcher
from spacy.parts_of_speech import VERB
from spacy.symbols import nsubj

nlp = spacy.load("en_core_web_lg")


class Quote:
    def __init__(self, doc=None, quote=None, start=None, end=None, prefix=None, suffix=None, do_not_init=False):
        if not do_not_init:
            self.doc = doc
            self.quote = quote
            self.start = start
            self.end = end
            self.prefix = prefix if prefix is not None else start
            self.suffix = suffix if suffix is not None else end
            self.full_quote_str = self.clean(self.doc[self.prefix:self.suffix].text)
            self.prefix_str = self.clean(self.doc[self.prefix: self.start].text)
            self.quote_str = self.clean(self.doc[self.start: self.end].text)
            self.suffix_str = self.clean(self.doc[self.end: self.suffix].text)
            self.prefix_verbs = self.get_prefix_verbs()
            self.suffix_verbs = self.get_suffix_verbs()

    def clean(self, string):
        string = re.sub(r"\n", r" ", string)
        return re.sub(r"\s+", r" ", string)

    def __repr__(self):
        return str(self.quote_str)

    def to_dict(self):
        return {
            "prefix": self.prefix_str,
            "quote": self.quote_str,
            "full_quote": self.full_quote_str,
            "suffix": self.suffix_str,
            "prefix_verbs": list(self.prefix_verbs),
            "suffix_verbs": list(self.suffix_verbs)
        }

    @staticmethod
    def from_dict(dictionary):
        quote = Quote(do_not_init=True)
        quote.prefix_str = dictionary["prefix"]
        quote.quote_str = dictionary["quote"]
        quote.suffix_str = dictionary["suffix"]
        quote.prefix_verbs = dictionary["prefix_verbs"]
        quote.suffix_verbs = dictionary["suffix_verbs"]
        quote.full_quote_str = dictionary["full_quote"]
        return quote

    def get_prefix_verbs(self):
        return self.get_verbs(self.doc[self.prefix: self.start])

    def get_suffix_verbs(self):
        return self.get_verbs(self.doc[self.end: self.suffix])

    def get_verbs(self, doc):
        verbs = []
        for possible_subject in doc.noun_chunks:
            if possible_subject.root.dep == nsubj and possible_subject.root.head.pos == VERB:
                # need to add code for adverbs
                verbs.append(
                    {"noun": self.clean(possible_subject.text),
                     "verb": self.clean(possible_subject.root.head.text.lower())})
        return verbs


class QuoteExtractor:
    SPEAKERS_TO_AVOID = {'he', 'she', 'they', 'it'}
    QUOTE_PATTERN = [{"IS_QUOTE": True}, {"OP": "*"}, {"IS_QUOTE": False}, {"OP": "*"}, {"IS_QUOTE": True}]
    MATCHER = Matcher(nlp.vocab)
    MATCHER.add("quote", None, QUOTE_PATTERN)

    DEFAULT_INPUT_SEED_PATTERNS = [
        {"prefix": None, "suffix": "said"},
        {"prefix": "announced", "suffix": None},
    ]

    @staticmethod
    def create_readable_patterns(patterns):
        for pattern in patterns:
            QuoteExtractor._create_readable_pattern(pattern)

    @staticmethod
    def _create_readable_pattern(pattern):
        readable = ["START"]
        if pattern["prefix"] is not None:
            readable.append("QUOTE")
            readable.append(pattern["prefix"].lower())
            readable.append("SPEAKER")
        elif pattern["suffix"] is not None:
            readable.append("SPEAKER")
            readable.append(pattern["suffix"].lower())
            readable.append("QUOTE")
        readable.append("END")
        pattern["readable"] = readable
        pattern["readable_str"] = " ".join(readable)

    @staticmethod
    def augment_patterns_with_synonyms(patterns):
        for pattern in patterns:
            QuoteExtractor._augment_patterns_with_synonyms(patterns, pattern)

    @staticmethod
    def _augment_patterns_with_synonyms(patterns, pattern):
        if pattern["prefix"] is not None:
            verb = pattern["prefix"].lower()
            syns = QuoteExtractor.get_synonyms(verb)
            for syn in syns:
                print(syn)  # to do
        elif pattern["suffix"] is not None:
            verb = pattern["suffix"].lower()
            syns = QuoteExtractor.get_synonyms(verb)
            for syn in syns:
                print(syn)  # to do

    def __init__(self, nlp, min_occurences=5, input_patterns=None):
        self.discarded_patterns = set()
        self.min_occurences = min_occurences
        self.nlp = nlp
        if input_patterns is not None:
            self.SEED_PATTERNS = self.load_patterns(input_patterns)
        else:
            self.SEED_PATTERNS = QuoteExtractor.DEFAULT_INPUT_SEED_PATTERNS
        self.create_readable_patterns(self.SEED_PATTERNS)

    @staticmethod
    def get_synonyms(word):
        from nltk.corpus import wordnet
        synonyms = []
        for syn in wordnet.synsets(word):
            for l in syn.lemmas():
                synonyms.append(l.name())
        return set(synonyms)

    @staticmethod
    def get_single_line_quote(doc):
        quote_count = 0
        for token in doc:
            if token.is_quote:
                quote_count += 1
                if quote_count > 2:
                    return None
        return doc

    @staticmethod
    def get_quote_prefix(doc, current):
        return doc[current].sent.start

    @staticmethod
    def get_quote_suffix(doc, current):
        return doc[current].sent.end

    @staticmethod
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

    @staticmethod
    def try_match(pattern, quote, out_entity, verbose=False):
        if verbose:
            print(pattern)
        if pattern["prefix"] is not None:
            if verbose:
                print("looking for prefixes")
            for verb in quote.prefix_verbs:
                if verbose:
                    print("Found:", verb)
                if pattern["prefix"].lower() == verb["verb"]:
                    if verbose:
                        print("Found in pattern")
                    if verb["noun"].lower().strip() not in QuoteExtractor.SPEAKERS_TO_AVOID:
                        out_entity.append(verb["noun"].strip())
                else:
                    if verbose:
                        print("Not in pattern")
        if pattern["suffix"] is not None:
            if verbose:
                print("looking for suffixes")
            for verb in quote.suffix_verbs:
                if verbose:
                    print("Found:", verb)
                if pattern["suffix"].lower() == verb["verb"]:
                    if verbose:
                        print("Found in pattern")
                    if verb["noun"].lower().strip() not in QuoteExtractor.SPEAKERS_TO_AVOID:
                        out_entity.append(verb["noun"].strip())
                else:
                    if verbose:
                        print("Not in pattern")
        return len(out_entity) == 1

    @staticmethod
    def add_pattern_hit(pattern_hits, pattern, quote, entity):
        pattern = pattern["readable_str"]
        if pattern not in pattern_hits:
            pattern_hits[pattern] = []
        hit = {
            "quote": quote.quote_str,
            "speaker": entity
        }
        pattern_hits[pattern].append(hit)
        return hit

    def run_on_docs(self, num_docs=None, verbose=False, min_length=8, max_length=64, get_pattern_hits=False,
                    bootstrap=False, save=False):
        session = Session()
        docs = session.query(ReutersDoc)
        total_docs = docs.count()
        if num_docs is None:
            num_docs = total_docs
        quotes = {}
        pattern_hits = {}
        for document in docs[:num_docs]:
            self.from_doc(document, quotes, pattern_hits, verbose=verbose, get_pattern_hits=False,
                          min_length=min_length, max_length=max_length)

        if get_pattern_hits:
            if bootstrap:
                new_patterns_added = True
                self.discarded_patterns = set()
                while new_patterns_added:
                    pattern_hits = {}
                    new_patterns_added = self._get_pattern_hits(quotes, pattern_hits, verbose=verbose,
                                                                discarded_patterns=self.discarded_patterns)
            else:
                self._get_pattern_hits(quotes, pattern_hits, verbose=verbose)
        session.close()

        if save:
            with open("quotes.json", "w") as f:
                out_quotes = {}
                for _quote in quotes:
                    if _quote not in out_quotes:
                        out_quotes[_quote] = []
                    for quote in quotes[_quote]:
                        out_quotes[_quote].append(quote.to_dict())
                json.dump(out_quotes, f)
            with open("pattern_hits.json", "w") as f:
                json.dump(pattern_hits, f)

        return quotes, pattern_hits

    def run_on_file(self, file, verbose=False, get_pattern_hits=False,
                    bootstrap=False, save=False):
        quotes = {}
        pattern_hits = {}
        with open(file) as f:
            _quotes = json.load(f)

        for _quote in _quotes:
            if _quote not in quotes:
                quotes[_quote] = []
                for quote in _quotes[_quote]:
                    quotes[_quote].append(Quote.from_dict(quote))

        if get_pattern_hits:
            if bootstrap:
                new_patterns_added = True
                discarded_patterns = set()
                while new_patterns_added:
                    pattern_hits = {}
                    new_patterns_added = self._get_pattern_hits(quotes, pattern_hits, verbose=verbose,
                                                                discarded_patterns=discarded_patterns)
            else:
                self._get_pattern_hits(quotes, pattern_hits, verbose=verbose)

        if save:
            with open("pattern_hits.json", "w") as f:
                json.dump(pattern_hits, f)

        return quotes, pattern_hits

    def _get_pattern_hits(self, quotes, pattern_hits, verbose, discarded_patterns=None):
        original_pattern_count = len(self.SEED_PATTERNS)
        new_patterns = []
        if not discarded_patterns:
            discarded_patterns = set()
        for _quote in quotes:
            matched = 0
            matched_patterns = set()
            matched_quotes = set()
            for quote in quotes[_quote]:
                quote.matched = False
                if verbose:
                    print(quote)
                for pattern in self.SEED_PATTERNS:
                    if pattern["readable_str"] in discarded_patterns:
                        continue
                    ents = []
                    matches = self.try_match(pattern, quote, ents, verbose)
                    if matches:
                        if not quote.matched:
                            matched += 1
                            quote.matched = True
                        if verbose:
                            print()
                            print("=" * 80)
                            print("Matched Pattern: ", pattern["readable_str"])
                        hit = self.add_pattern_hit(pattern_hits, pattern, quote, ents[0])
                        if verbose:
                            print(hit)
                            print("=" * 80)
                            print()

                        matched_patterns.add(pattern["readable_str"])
                        matched_quotes.add(quote)

                    else:
                        pattern = pattern["readable_str"]
                        if pattern not in pattern_hits:
                            pattern_hits[pattern] = []
            if matched > 0 and matched != len(quotes[_quote]):
                for quote in quotes[_quote]:
                    if quote not in matched_quotes:
                        if quote.prefix_verbs:
                            for verb in quote.prefix_verbs:
                                if verb["noun"] in (
                                        [verb["noun"] for verb in quote.prefix_verbs for quote in matched_quotes] +
                                        [verb["noun"] for verb in quote.suffix_verbs for quote in matched_quotes]):
                                    pattern = {"prefix": verb["verb"], "suffix": None}
                                    QuoteExtractor._create_readable_pattern(pattern)
                                    if pattern not in new_patterns and pattern[
                                        "readable_str"] not in discarded_patterns:
                                        new_patterns.append(pattern)

                        if quote.suffix_verbs:
                            for verb in quote.suffix_verbs:
                                if verb["noun"] in (
                                        [verb["noun"] for verb in quote.prefix_verbs for quote in matched_quotes] +
                                        [verb["noun"] for verb in quote.suffix_verbs for quote in matched_quotes]):
                                    pattern = {"prefix": verb["verb"], "suffix": None}
                                    QuoteExtractor._create_readable_pattern(pattern)
                                    if pattern not in new_patterns and pattern[
                                        "readable_str"] not in discarded_patterns:
                                        new_patterns.append(pattern)

            if verbose:
                print("_" * 80)
                print()
        for pattern in pattern_hits:
            if len(pattern_hits[pattern]) < self.min_occurences:
                discarded_patterns.add(pattern)
        for pattern in new_patterns:
            if pattern["readable_str"] not in discarded_patterns and pattern not in self.SEED_PATTERNS:
                self.SEED_PATTERNS.append(pattern)
        new_pattern_count = len(self.SEED_PATTERNS)
        return new_pattern_count > original_pattern_count

    def from_doc(self, document, quotes=None, pattern_hits=None, get_pattern_hits=False, verbose=False, min_length=8,
                 max_length=64):
        if quotes is None:
            quotes = {}
        if pattern_hits is None:
            pattern_hits = {}
        self._from_doc(document.body, quotes, min_length, max_length)

        if get_pattern_hits:
            self._get_pattern_hits(quotes, pattern_hits, verbose)
        return quotes, pattern_hits

    def _from_doc(self, text, quotes, min_length=8, max_length=64):
        doc = self.nlp(text)
        matches = self.MATCHER(doc)
        odd = True
        for match_id, start, end in matches:
            quote = self.get_single_line_quote(doc[start:end])
            if quote is not None:
                if odd and min_length < len(quote) <= max_length:
                    quote = Quote(doc, quote, start, end, self.get_quote_prefix(doc, start),
                                  self.get_quote_suffix(doc, end))
                    if quote.quote_str not in quotes:
                        quotes[quote.quote_str] = []
                    quotes[quote.quote_str].append(quote)
                odd = not odd

    def save_patterns(self, file):
        with open(file, 'w') as f:
            json.dump(self.SEED_PATTERNS, f)

    @staticmethod
    def load_patterns(file):
        with open(file) as f:
            return json.load(f)

# Start here

# Creates a quotes.json file if save=True
# runs on the reuters dataset
# has an optional num_docs argument to run on a smaller set (eg: num_docs=10)
# quotes, pattern_hits = (QuoteExtractor(nlp).run_on_docs(get_pattern_hits=False, verbose=False, bootstrap=False,
#                                                         save=True))


# loads a file (saved from the previous function) to avoid extracting quotes again
# quotes, pattern_hits = (
#     QuoteExtractor(nlp).run_on_file("quotes.json", get_pattern_hits=True, verbose=False, bootstrap=True,
#                                     save=True))


# to display

# pprint(quotes)
# pprint(pattern_hits)
# for key in pattern_hits:
#     print(key, len(pattern_hits[key]))
