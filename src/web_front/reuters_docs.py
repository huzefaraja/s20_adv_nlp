from pprint import pprint

from extractors import quote_extractor
from extractors.quote_extractor import nlp
from flask import Blueprint, render_template, request, redirect, url_for

from . import db
from .models import ReutersDoc, SeedSentences

reuters_docs = Blueprint('reuters_docs', __name__)


@reuters_docs.route('/reuters_dataset')
def reuters_dataset():
    docs = ReutersDoc.query.all()
    return render_template('reuters_dataset.html', docs=docs)


def transform_pattern_hits(pattern_hits):
    out_dict = {}
    for pattern in pattern_hits:
        for hit in pattern_hits[pattern]:
            speaker = hit["speaker"]
            quote = hit["quote"]
            if speaker not in out_dict:
                out_dict[speaker] = []
            out_dict[speaker].append(quote)
    return out_dict


@reuters_docs.route('/view_page')
def view_page():
    id = request.args.get('id', default=1, type=int)
    doc = ReutersDoc.query.filter_by(id=id).first()
    quotes, pattern_hits = quote_extractor.QuoteExtractor(nlp).from_doc(doc, get_pattern_hits=True)
    return render_template('view_page.html', doc=doc, quotes=transform_pattern_hits(pattern_hits))


@reuters_docs.route('/seed_sentence_submit', methods=["POST"])
def seed_sentence_submit():
    print("SEED")

    print(request.form)
    begin_offset = request.form['start_offset']
    print("slfkjas")
    end_offset = request.form['end_offset']
    sentence_text = request.form['sentence_text']
    doc_id = request.form['document_id']

    new_sentence = SeedSentences(reuters_doc_id=int(doc_id),
                                 begin_offset=begin_offset,
                                 end_offset=end_offset,
                                 sentence_text=sentence_text)
    db.session.add(new_sentence)
    db.session.commit()
    print("OFFEST")
    return redirect(url_for('view_pageid=?' + str(doc_id)))
