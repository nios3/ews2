import os
from twilio import Client

account_sid = os.environ.get('sid')
auth_token = os.environ.get('auth')


client = Client(account_sid, auth_token)

message = client.messages \
    .create(
         body='all farmers information and details..................... ',
         from_='+25476822441',

         to='+254748650711'
     )

print(message.sid)