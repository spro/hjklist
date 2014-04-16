import requests
import config

def send_mail(to_address, from_address, subject, message_text, message_html):
    print requests.post("https://api.mailgun.net/v2/hjklist.mailgun.org/messages", auth=('api', config.mailgun_api_key), data={
        'to': to_address,
        'from': from_address,
        'subject': subject,
        'text': message_text,
        'html': message_html
    })
