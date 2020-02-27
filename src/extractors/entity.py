

class Entity:
    def __init__(self, entity_text, entity_type):
        self.entity_text = entity_text
        self.entity_type = entity_type

    def get_entity_text(self):
        return self.entity_text

    def get_entity_type(self):
        return self.entity_type