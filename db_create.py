from FlaskProject import db
from FlaskProject.models import *
from datetime import date

db.create_all()

db.session.commit()