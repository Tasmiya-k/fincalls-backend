# models.py
from flask_mongoengine import MongoEngine

db = MongoEngine()

class Fincalls(db.Document):
    id = db.StringField(primary_key=True)
    audio_file = db.FileField()
    transcript_file = db.FileField()
    summarization_file = db.FileField()
