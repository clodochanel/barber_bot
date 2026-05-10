from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # Add this to fix connection issues
from database import db, Conversation, Booking
from barber_bot import BarberBot
from datetime import datetime

app = Flask(__name__)
CORS(app)  # This fixes connection problems

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barber.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables when app starts
with app.app_context():
    db.create_all()

# Store bot sessions (one per customer)
sessions = {}

@app.route('/')
def dashboard():
    """Barber sees all conversations and bookings"""
    conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(50).all()
    bookings = Booking.query.order_by(Booking.timestamp.desc()).all()
    return render_template('dashboard.html', conversations=conversations, bookings=bookings)

@app.route('/chat', methods=['POST'])
def chat():
    """The API that the chatbot widget calls"""
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        user_message = data.get('message', '')
        
        print(f"Received message: {user_message} from session {session_id}")  # Debug print
        
        # Get or create bot for this session
        if session_id not in sessions:
            sessions[session_id] = BarberBot()
            print(f"Created new bot for session {session_id}")
        
        bot = sessions[session_id]
        bot_response = bot.get_response(user_message)
        
        print(f"Bot response: {bot_response}")  # Debug print
        
        # Save to database for barber to see
        conv = Conversation(
            customer_name=bot.booking_data.get('name', 'Anonymous'),
            customer_phone=bot.booking_data.get('phone', ''),
            message=user_message,
            bot_response=bot_response
        )
        db.session.add(conv)
        db.session.commit()
        
        # If booking is complete, save it separately
        if "✅ Booked!" in bot_response:
            booking = Booking(
                customer_name=bot.booking_data.get('name', ''),
                customer_phone=bot.booking_data.get('phone', ''),
                service=bot.booking_data.get('service', ''),
                date=bot.booking_data.get('date', ''),
                time=bot.booking_data.get('time', '')
            )
            db.session.add(booking)
            db.session.commit()
            print(f"Saved booking for {booking.customer_name}")  # Debug print
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'response': bot_response
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'response': 'Sorry, something went wrong. Please try again.'})
@app.route('/delete_conversation/<int:id>', methods=['POST'])
def delete_conversation(id):
    """Delete a single conversation"""
    conv = Conversation.query.get_or_404(id)
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Conversation deleted'})

@app.route('/delete_booking/<int:id>', methods=['POST'])
def delete_booking(id):
    """Delete a single booking"""
    booking = Booking.query.get_or_404(id)
    db.session.delete(booking)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Booking deleted'})

@app.route('/reset_all_data', methods=['POST'])
def reset_all_data():
    """DELETE ALL DATA - Reset everything"""
    try:
        # Delete all conversations
        num_conversations = Conversation.query.delete()
        # Delete all bookings
        num_bookings = Booking.query.delete()
        # Commit the changes
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Deleted {num_conversations} conversations and {num_bookings} bookings'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_old_data', methods=['POST'])
def delete_old_data():
    """Delete data older than X days"""
    data = request.json
    days = data.get('days', 30)  # Default: delete older than 30 days
    
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old conversations
    old_conversations = Conversation.query.filter(Conversation.timestamp < cutoff_date).delete()
    # Delete old bookings
    old_bookings = Booking.query.filter(Booking.timestamp < cutoff_date).delete()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Deleted {old_conversations} conversations and {old_bookings} bookings older than {days} days'
    })

@app.route('/api/stats')
def api_stats():
    """Get dashboard statistics as JSON"""
    total_conversations = Conversation.query.count()
    total_bookings = Booking.query.count()
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    today_conversations = Conversation.query.filter(Conversation.timestamp >= today_start).count()
    today_bookings = Booking.query.filter(Booking.timestamp >= today_start).count()
    
    # Get last 7 days of conversations for chart
    from datetime import timedelta
    last_7_days = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = Conversation.query.filter(
            Conversation.timestamp >= datetime(date.year, date.month, date.day),
            Conversation.timestamp < datetime(next_date.year, next_date.month, next_date.day)
        ).count()
        last_7_days.append({'date': date.strftime('%m/%d'), 'count': count})
    
    return jsonify({
        'total_conversations': total_conversations,
        'total_bookings': total_bookings,
        'today_conversations': today_conversations,
        'today_bookings': today_bookings,
        'last_7_days': last_7_days
    })

@app.route('/api/bookings')
def api_bookings():
    """Return all bookings as JSON"""
    bookings = Booking.query.order_by(Booking.timestamp.desc()).all()
    return jsonify([b.to_dict() for b in bookings])

@app.route('/api/conversations')
def api_conversations():
    """Return all conversations as JSON"""
    conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(100).all()
    return jsonify([c.to_dict() for c in conversations])


@app.route('/widget.js')
def widget():
    """The JavaScript snippet barbers put on their website"""
    js_code = """
    // Barber Bot Widget - Fixed Version
    (function() {
        console.log("Barber Bot Widget loading...");
        
        // Create chat button
        const button = document.createElement('div');
        button.innerHTML = '💈 Chat';
        button.style.position = 'fixed';
        button.style.bottom = '20px';
        button.style.right = '20px';
        button.style.backgroundColor = '#1a1a1a';
        button.style.color = 'white';
        button.style.padding = '12px 20px';
        button.style.borderRadius = '30px';
        button.style.cursor = 'pointer';
        button.style.fontFamily = 'Arial, sans-serif';
        button.style.fontWeight = 'bold';
        button.style.zIndex = '9999';
        button.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        
        // Create chat window (hidden initially)
        const chatWindow = document.createElement('div');
        chatWindow.style.position = 'fixed';
        chatWindow.style.bottom = '80px';
        chatWindow.style.right = '20px';
        chatWindow.style.width = '350px';
        chatWindow.style.height = '500px';
        chatWindow.style.backgroundColor = 'white';
        chatWindow.style.borderRadius = '10px';
        chatWindow.style.boxShadow = '0 5px 20px rgba(0,0,0,0.3)';
        chatWindow.style.display = 'none';
        chatWindow.style.flexDirection = 'column';
        chatWindow.style.zIndex = '9999';
        chatWindow.style.fontFamily = 'Arial, sans-serif';
        
        chatWindow.innerHTML = `
            <div style="background:#1a1a1a; color:white; padding:15px; border-radius:10px 10px 0 0; font-weight:bold;">
                💈 Barber Shop Assistant
                <span id="closeChat" style="float:right; cursor:pointer;">✕</span>
            </div>
            <div id="chatMessages" style="flex:1; padding:15px; overflow-y:auto; background:#f9f9f9;">
                <div style="margin-bottom:10px;">
                    <div style="background:#1a1a1a; color:white; padding:8px 12px; border-radius:15px; display:inline-block; max-width:80%;">
                        Hello! Ask me about hours, prices, or book an appointment.
                    </div>
                </div>
            </div>
            <div style="padding:15px; border-top:1px solid #ddd; display:flex;">
                <input type="text" id="chatInput" placeholder="Type your message..." style="flex:1; padding:8px; border:1px solid #ddd; border-radius:20px; margin-right:10px;">
                <button id="sendBtn" style="background:#1a1a1a; color:white; border:none; border-radius:20px; padding:8px 15px; cursor:pointer;">Send</button>
            </div>
        `;
        
        document.body.appendChild(button);
        document.body.appendChild(chatWindow);
        
        let sessionId = localStorage.getItem('barber_session');
        if (!sessionId) {
            sessionId = Math.random().toString(36).substring(7);
            localStorage.setItem('barber_session', sessionId);
        }
        
        console.log("Session ID:", sessionId);
        
        button.onclick = () => {
            chatWindow.style.display = 'flex';
        };
        
        document.getElementById('closeChat').onclick = () => {
            chatWindow.style.display = 'none';
        };
        
        const sendMessage = () => {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;
            
            console.log("Sending message:", message);
            
            // Add user message to chat
            const messagesDiv = document.getElementById('chatMessages');
            const userMsgDiv = document.createElement('div');
            userMsgDiv.style.textAlign = 'right';
            userMsgDiv.style.marginBottom = '10px';
            userMsgDiv.innerHTML = `<div style="background:#007bff; color:white; padding:8px 12px; border-radius:15px; display:inline-block; max-width:80%;">${message.replace(/</g, '&lt;')}</div>`;
            messagesDiv.appendChild(userMsgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            input.value = '';
            
            // Show typing indicator
            const typingDiv = document.createElement('div');
            typingDiv.style.marginBottom = '10px';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = `<div style="background:#e9ecef; color:#666; padding:8px 12px; border-radius:15px; display:inline-block;">Bot is typing...</div>`;
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            // Send to server
            fetch('https://barber-bot-j4if.onrender.com/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                // Remove typing indicator
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
                
                console.log("Got response:", data);
                
                if (data.success !== false) {
                    const botMsgDiv = document.createElement('div');
                    botMsgDiv.style.marginBottom = '10px';
                    botMsgDiv.innerHTML = `<div style="background:#e9ecef; color:#333; padding:8px 12px; border-radius:15px; display:inline-block; max-width:80%;">${data.response.replace(/</g, '&lt;')}</div>`;
                    messagesDiv.appendChild(botMsgDiv);
                } else {
                    const errMsgDiv = document.createElement('div');
                    errMsgDiv.style.marginBottom = '10px';
                    errMsgDiv.innerHTML = `<div style="background:#f8d7da; color:#721c24; padding:8px 12px; border-radius:15px; display:inline-block;">Sorry, there was an error. Please try again.</div>`;
                    messagesDiv.appendChild(errMsgDiv);
                }
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            })
            .catch(error => {
                console.error('Error:', error);
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
                
                const errMsgDiv = document.createElement('div');
                errMsgDiv.style.marginBottom = '10px';
                errMsgDiv.innerHTML = `<div style="background:#f8d7da; color:#721c24; padding:8px 12px; border-radius:15px; display:inline-block;">Cannot connect to server. Make sure the bot is running.</div>`;
                messagesDiv.appendChild(errMsgDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            });
        };
        
        document.getElementById('sendBtn').onclick = sendMessage;
        document.getElementById('chatInput').onkeypress = (e) => {
            if (e.key === 'Enter') sendMessage();
        };
    })();
    """
    return js_code, 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='127.0.0.1')