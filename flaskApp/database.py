from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()




class exampleTable(db.Model):
    example = db.Column(db.Integer, primary_key=True)
   

    def __repr__(self):
        return 'example table'


##Creates the table
def create_database(app):
    with app.app_context():
        db.create_all()