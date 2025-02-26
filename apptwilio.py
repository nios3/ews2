# Twilio-WayScript API
from flask import Flask, request, jsonify
from twilio.rest import Client
import os
from db import get_db_connection
import config

app = Flask(__name__)

# Add this line to initialize the client globally
client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

@app.route('/', methods=['GET','POST'])
def send_message():
    if request.method == 'POST':
        sid = os.environ.get('sid')
        auth = os.environ.get('auth')

        data = request.get_json()
        if data.get('body') is None or data.get('to') is None:
            return 'Key "body" or "to" not defined.'
        if not sid or not auth:
            return 'Missing SID or Auth token'

        client = Client(sid, auth)
        msg_to = data.get('to')
        msg_body = data.get('body')
        message = client.messages.create(
            body=msg_body,
            from_='+254768224441',
            to=msg_to
        )
        print(message.sid)
        return 'Message Sent to {}'.format(msg_to)

@app.route('/send-messages', methods=['GET'])
def send_messages():
    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query all phone numbers
        cursor.execute("SELECT phone_numb FROM farmers_details")
        farmers = cursor.fetchall()

        # Message content
        message_body = "Hello Farmer, this is an early warning system alert!"

        # Send SMS to each farmer
        for farmer in farmers:
            phone_number = farmer[0]  # Extract phone number from tuple
            client.messages.create(
                body=message_body,
                from_=config.TWILIO_PHONE_NUMBER,
                to=phone_number
            )

        # Close connection
        cursor.close()
        conn.close()

        return jsonify({"status": "Messages sent to all farmers"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)