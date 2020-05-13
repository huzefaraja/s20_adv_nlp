import sqlalchemy as db
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = db.create_engine(
    # 'mysql+mysqlconnector://nlpuser:nlpuserpassword@localhost:3306/gw_nlp?charset=utf8',
    'mysql+pymysql://nlpuser:nlpuserpassword@localhost:3306/gw_nlp?charset=utf8'
    #     echo=True
)
connection = engine.connect()
metadata = db.MetaData()

Base = declarative_base()


class ReutersDoc(Base):
    __tablename__ = 'reuters_docs'
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.String(length=255), index=True)
    categories = db.Column(db.String(length=255))
    body = db.Column(db.TEXT())


class ReutersQuote(Base):
    __tablename__ = 'reuters_quote'
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.String(length=255), index=True)
    _doc_id = db.Column(db.Integer, db.ForeignKey("reuters_docs.id"))
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    prefix = db.Column(db.Integer)
    suffix = db.Column(db.Integer)
    body = db.Column(db.TEXT())
    entity_start = db.Column(db.Integer)
    entity_end = db.Column(db.Integer)
    entity_id = db.Column(db.Integer, db.ForeignKey("reuters_entity.id"))


class ReutersEntity(Base):
    __tablename__ = 'reuters_entity'
    id = db.Column(db.Integer, primary_key=True)
    doc_id = db.Column(db.String(length=255), index=True)
    _doc_id = db.Column(db.Integer, db.ForeignKey("reuters_docs.id"))
    start = db.Column(db.Integer)
    end = db.Column(db.Integer)
    name = db.Column(db.String(length=255), index=True)
    type = db.Column(db.String(length=50))


Session = sessionmaker(bind=engine)
