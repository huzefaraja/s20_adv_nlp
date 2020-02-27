class Document:

    def __init__(self, document_id, text):
        self.document_id = document_id
        self.text = text
        self.mentions = []

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text

    def add_mention(self, mention):
        self.mentions.append(mention)

    def get_mentions(self):
        return self.mentions