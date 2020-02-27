

class Mention:
    def __init__(self, mention, document, start_offset, end_offset):
        self.mention = mention
        self.document = document
        self.start_offset = start_offset
        self.end_offset = end_offset
        self.entities = None

    def get_mention(self):
        return self.mention

    def get_document(self):
        return self.document

    def add_entity(self, entity):
        self.entities.append(entity)

    def add_entities(self, entities):
        self.entities = entities