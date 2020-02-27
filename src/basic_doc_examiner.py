from data_sources import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import urllib.request
import nltk
import spacy

from extractors import *


documents = session.query(ReutersDoc).all()

nlp = spacy.load("en")

list_of_targets = [["GPE", "ORG"], ["LOC", "ORG"], ["PERSON", "ORG"]]


tracking_docs = []
tracking_mentions = []
for index, document in enumerate(documents):
    doc = nlp(document.body)
    tracking_document = Document(document.id, document.body)

    for sentence in doc.sents:
        sentence_doc = sentence.as_doc()
        if len(sentence_doc.ents) > 1:
            entities = [Entity(entity.text, entity.label_) for entity in sentence_doc.ents if len(entity.text.strip()) > 0]
            entities_with_type = [entity.label_ for entity in sentence_doc.ents if
                        len(entity.text.strip()) > 0]

            for seed_entities in list_of_targets:
                candidate_sentence = []

                for entity_type in seed_entities:
                    if entities_with_type.count(entity_type) == 1:
                        candidate_sentence.append(1)
                    elif entities_with_type.count(entity_type) > 1:
                        break
                if sum(candidate_sentence) == 2:
                    mention = Mention(sentence.text, tracking_document, sentence.start_char, sentence.end_char)
                    mention.add_entities(entities)
                    print("Sentence has these entities: ", entities_with_type)
                    print("\t", sentence.text)
                    print("\tSentence is a candidate")
                    print("*&" * 25)
                    tracking_document.add_mention(mention)
                    tracking_mentions.append(mention)
    if index == 500:
        break
print(tracking_mentions)