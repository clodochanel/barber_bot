import re

class BarberBot:
    def __init__(self):
        self.intents = {
            "hours": ["hour", "open", "close", "when", "schedule", "time"],
            "prices": ["price", "cost", "how much", "charge", "dollar", "$"],
            "location": ["where", "address", "location", "street", "area"],
            "haircut": ["haircut", "cut", "trim", "fade", "taper"],
            "beard": ["beard", "shave", "trim beard"],
            "book": ["book", "appointment", "reserve", "schedule", "come in", "visit"],
            "contact": ["phone", "call", "whatsapp", "contact", "number"]
        }
        
        self.responses = {
            "hours": "We're open Tuesday-Saturday 9 AM to 7 PM. Closed Sunday-Monday.",
            "prices": "Haircut: $25 | Beard trim: $15 | Haircut + Beard: $35 | Kids cut: $18",
            "location": "We're at 123 Main Street, downtown. Right next to Starbucks.",
            "haircut": "We do all types: fades, scissor cuts, tapers. $25.",
            "beard": "Beard trim is $15, hot towel shave is $20.",
            "contact": "Call or WhatsApp us at (555) 123-4567",
            "book": "Sure! Let me help you book. What's your name?"
        }
        
        # Memory for booking
        self.waiting_for = None
        self.booking_data = {
            'name': '',
            'phone': '',
            'service': '',
            'date': '',
            'time': ''
        }
    
    def get_response(self, message):
        message = message.lower().strip()
        
        # STEP 1: Check if we're in the middle of booking
        if self.waiting_for == "name":
            self.booking_data['name'] = message
            self.waiting_for = "phone"
            return "Great! Now your phone number (so we can confirm):"
        
        if self.waiting_for == "phone":
            # Accept any phone number format
            self.booking_data['phone'] = message
            self.waiting_for = "service"
            return "Thanks! What service? (haircut, beard, or both)"
        
        if self.waiting_for == "service":
            if "haircut" in message and "beard" in message:
                self.booking_data['service'] = "Haircut + Beard ($35)"
            elif "haircut" in message:
                self.booking_data['service'] = "Haircut ($25)"
            elif "beard" in message:
                self.booking_data['service'] = "Beard trim ($15)"
            else:
                return "Please choose: haircut, beard, or both"
            
            self.waiting_for = "date"
            return "What day works for you? (e.g., Tuesday, March 15th, or tomorrow)"
        
        if self.waiting_for == "date":
            self.booking_data['date'] = message
            self.waiting_for = "time"
            return "What time? We're open 9 AM - 7 PM. Example: 2:30 PM"
        
        if self.waiting_for == "time":
            self.booking_data['time'] = message
            
            # Booking complete - save data
            booking_info = self.booking_data.copy()
            
            # Reset for next conversation
            self.waiting_for = None
            self.booking_data = {
                'name': '',
                'phone': '',
                'service': '',
                'date': '',
                'time': ''
            }
            
            return f"✅ Booked! {booking_info['name']}, {booking_info['service']} on {booking_info['date']} at {booking_info['time']}. We'll text you at {booking_info['phone']} to confirm. See you!"
        
        # STEP 2: Normal conversation
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in message:
                    if intent == "book":
                        self.waiting_for = "name"
                        self.booking_data = {
                            'name': '', 'phone': '', 'service': '', 'date': '', 'time': ''
                        }
                        return self.responses["book"]
                    return self.responses[intent]
        
        return "I can help with hours, prices, location, or booking. Type 'book' to make an appointment."
    
    def get_booking_data(self):
        """Return the current booking data (for saving to database)"""
        return self.booking_data