from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    bot_response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'message': self.message,
            'bot_response': self.bot_response[:100] + '...' if len(self.bot_response) > 100 else self.bot_response,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M')
        }

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    service = db.Column(db.String(100))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'service': self.service,
            'date': self.date,
            'time': self.time,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M')
        }