import pydotenv
import threading
from getpass import getpass
from flask import Flask

from BandwidthSmsHandler import BandwidthSmsHandler
from MessengerHandler import MessengerHandler
from SMSOutgoingMiddleman import SMSOutgoingMiddleman
from TwilioSmsHandler import TwilioSmsHandler


def get_sms_provider(provider_name, environment):
    to_number = environment.get('YOUR_NUMBER')
    if provider_name == 'bandwidth':
        return BandwidthSmsHandler(
            environment.get('BANDWIDTH_USER'),
            environment.get('BANDWIDTH_TOKEN'),
            environment.get('BANDWIDTH_SECRET'),
            environment.get('BANDWIDTH_FROM_NUMBER'),
            to_number
        )
    elif provider_name == 'twilio':
        return TwilioSmsHandler(
            environment.get('TWILIO_SID'),
            environment.get('TWILIO_AUTH_TOKEN'),
            environment.get('TWILIO_FROM_NUMBER'),
            to_number
        )
    else:
        raise ValueError('Bad SMS_PROVIDER in .env. Choices are: [bandwidth, twilio]')


def sms_to_messenger(flask_listener, sms_handler, message_handler, host, port):
    sms_handler.register_with_flask(flask)
    sms_handler.start(message_handler.sms_to_messenger)
    flask_listener.run(host=host, port=port, debug=False)


def messenger_to_sms(fb, message_handler):
    fb.start(message_handler.messenger_to_sms)


if __name__ == '__main__':
    env = pydotenv.Environment(check_file_exists=True)

    flask = Flask(__name__)

    fbmessenger = MessengerHandler(
        env.get('MESSENGER_LOGIN'),
        getpass('Messenger password: ')
    )
    sms_listener = get_sms_provider(env.get('SMS_PROVIDER'), env)
    middleman = SMSOutgoingMiddleman(fbmessenger.send_callback, sms_listener.send_callback)
    sms_to_messenger_thread = threading.Thread(target=sms_to_messenger, args=[
        flask,
        sms_listener,
        middleman,
        env.get('FLASK_HOST', None),
        env.get('FLASK_PORT', '5000')
    ])
    messenger_to_sms_thread = threading.Thread(target=messenger_to_sms, args=[fbmessenger, middleman])
    sms_to_messenger_thread.start()
    messenger_to_sms_thread.start()
