from extensions import db

class User(db.Model):
    __tablename__ = 'Users'

    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fullName = db.Column('FullName', db.String(255), nullable=False)
    email = db.Column('Email', db.String(120), unique=True, nullable=False)
    phone = db.Column('Phone', db.String(20), nullable=False)
    passwordHash = db.Column('PasswordHash', db.String(128), nullable=False)
    createdAt = db.Column('CreatedAt', db.DateTime, nullable=False)
    updatedAt = db.Column('UpdatedAt', db.DateTime, nullable=True)
    typeID = db.Column('TypeID', db.Integer, nullable=False, default=2)

    def __repr__(self):
        return f'<User {self.email}>'
