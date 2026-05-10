from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'Barber Bot is running on Render!'

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.json
        message = data.get('message', '').lower()
        
        if 'hour' in message or 'open' in message:
            response = "We're open Tuesday-Saturday 9am-7pm"
        elif 'price' in message or 'cost' in message:
            response = "Haircut $25, Beard $15, Haircut+Beard $35"
        elif 'book' in message or 'appointment' in message:
            response = "Sure! Let me help you book. What's your name?"
        else:
            response = "I can help with hours, prices, or booking appointments!"
        
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'response': str(e)})

@app.route('/widget.js')
def widget():
    from flask import request
    base_url = request.url_root.rstrip('/')
    
    js_code = f'''
    (function() {{
        console.log("Barber Bot Widget loading...");
        const API_URL = "{base_url}";
        
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
        button.style.fontFamily = 'Arial';
        button.style.fontWeight = 'bold';
        button.style.zIndex = '9999';
        button.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        
        // Create chat window
        const chatWindow = document.createElement('div');
        chatWindow.style.position = 'fixed';
        chatWindow.style.bottom = '80px';
        chatWindow.style.right = '20px';
        chatWindow.style.width = '350px';
        chatWindow.style.height = '450px';
        chatWindow.style.backgroundColor = 'white';
        chatWindow.style.borderRadius = '10px';
        chatWindow.style.boxShadow = '0 5px 20px rgba(0,0,0,0.3)';
        chatWindow.style.display = 'none';
        chatWindow.style.flexDirection = 'column';
        chatWindow.style.zIndex = '9999';
        
        chatWindow.innerHTML = `
            <div style="background:#1a1a1a; color:white; padding:15px; border-radius:10px 10px 0 0;">
                Barber Shop Assistant
                <span id="closeChat" style="float:right; cursor:pointer;">✕</span>
            </div>
            <div id="chatMessages" style="flex:1; padding:15px; overflow-y:auto; background:#f9f9f9;">
                <div style="margin-bottom:10px;">
                    <div style="background:#1a1a1a; color:white; padding:8px 12px; border-radius:15px; display:inline-block;">
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
        if (!sessionId) {{
            sessionId = Math.random().toString(36).substring(7);
            localStorage.setItem('barber_session', sessionId);
        }}
        
        button.onclick = () => chatWindow.style.display = 'flex';
        document.getElementById('closeChat').onclick = () => chatWindow.style.display = 'none';
        
        const sendMessage = () => {{
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chatMessages');
            const userMsgDiv = document.createElement('div');
            userMsgDiv.style.textAlign = 'right';
            userMsgDiv.style.marginBottom = '10px';
            userMsgDiv.innerHTML = `<div style="background:#007bff; color:white; padding:8px 12px; border-radius:15px; display:inline-block;">${{message.replace(/</g, '&lt;')}}</div>`;
            messagesDiv.appendChild(userMsgDiv);
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            fetch(API_URL + '/chat', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{session_id: sessionId, message: message}})
            }})
            .then(res => res.json())
            .then(data => {{
                const botMsgDiv = document.createElement('div');
                botMsgDiv.style.marginBottom = '10px';
                botMsgDiv.innerHTML = `<div style="background:#e9ecef; color:#333; padding:8px 12px; border-radius:15px; display:inline-block;">${{data.response}}</div>`;
                messagesDiv.appendChild(botMsgDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }})
            .catch(error => {{
                console.error('Error:', error);
                const errMsgDiv = document.createElement('div');
                errMsgDiv.style.marginBottom = '10px';
                errMsgDiv.innerHTML = `<div style="background:#f8d7da; color:#721c24; padding:8px 12px; border-radius:15px;">Connection error</div>`;
                messagesDiv.appendChild(errMsgDiv);
            }});
        }};
        
        document.getElementById('sendBtn').onclick = sendMessage;
        document.getElementById('chatInput').onkeypress = (e) => {{
            if (e.key === 'Enter') sendMessage();
        }};
    }})();
    '''
    return js_code, 200, {'Content-Type': 'application/javascript'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)