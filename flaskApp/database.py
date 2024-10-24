from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column


db=SQLAlchemy()

##User
class User(db.Model):
    __tablename__ = 'user' 
    email= db.Column(db.String, primary_key=True)
    username = db.Column(db.String, primary_key=False, nullable=False)
    password = db.Column(db.String, primary_key=False, nullable=False)
    status = db.Column(db.Integer, primary_key=False, nullable=False)
                      
    def __repr__(self):
        return '<userNamw %r>' % self.username
    
##Projects

class Projects(db.Model):
    __tablename__ = 'projects' 
    projectName= db.Column(db.String, primary_key=True)
    projectCode = db.Column(db.String, primary_key=False, nullable=False, unique=True)
    piCreator = db.Column(db.String, nullable=False)  # Reference user email
    
    # Define the relationship correctly
   
                      
    def __repr__(self):
        return '<Project Name %r>' % self.projectName




class Involvement(db.Model):
    id= db.Column(db.Integer, primary_key=True,
                index=True, autoincrement=True)

    user_id = mapped_column(ForeignKey("user.email"), primary_key=True)
    project_id = mapped_column(ForeignKey("projects.projectName"), primary_key=True)
   
    
   
    
    userss = relationship("User", foreign_keys=[user_id])
    projectss = relationship("Projects", foreign_keys=[project_id])
    



                      
   
    

##Creates the table
def create_database(app):
    with app.app_context():
        db.create_all()