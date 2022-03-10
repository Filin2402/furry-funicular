import logging
from logging import StreamHandler, Formatter
import sys
from datetime import datetime
import json
from smtplib import SMTPException

from mailing_out.parser import load_account
from service.operations import get_email_suffix
from mailing_out.resolvers import SMTPResolver


def configure_logger():
    handler = StreamHandler(stream=sys.stdout)
    handler.setFormatter(Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
    logging.basicConfig(level='INFO', handlers=[handler])


def do_sending_messages(senders: list, recipients: list,
                        message: str, client_resolver: SMTPResolver,
                        messages_amount: int = None,
                        summary_interval: float = 20):
    send_labels = dict()
    time_label = datetime.now().timestamp()
    summary_time_label = datetime.now().timestamp()
    position = 0
    for sender in senders:
        send_labels[sender] = time_label - sender.quota.\
            seconds_interval
    summary_sent = 0
    while messages_amount is None or summary_sent < messages_amount:
        if (datetime.now().timestamp() - summary_time_label
                > summary_interval):
            logging.info(f"Summary sent {summary_sent}")
            summary_time_label = datetime.now().timestamp()
        for sender in senders:
            interval = sender.quota.seconds_interval
            at_once = sender.quota.messages_at_once
            messages = sender.quota.messages
            if datetime.now().timestamp() - send_labels[
                sender] < interval:
                continue
            client = client_resolver.get_client(get_email_suffix(
                sender.email))
            client.sender = sender
            sent_by_sender = 0
            try:
                client.connect()
                while sent_by_sender < messages:
                    if sent_by_sender + at_once > messages:
                        at_once = messages - sent_by_sender - 1
                    rec_at_once = recipients[
                                  position:position + at_once]
                    client.send_mail(rec_at_once, message)
                    summary_sent += at_once
                    position += at_once
                    if position >= len(recipients):
                        logging.info(f"Messages was sent to all "
                                     f"{len(recipients)} recipients")
                        position = 0
                    sent_by_sender += at_once
            except SMTPException as e:
                logging.info(f"Sending message error at sender '"
                             f"{sender}'. Code '{e.errno}'."
                             f" Message: '{e.strerror}'")
            finally:
                client.disconnect()
                send_labels[sender] = datetime.now().timestamp()


def main():
    '''Senders file example senders.json
    [
        {
            'email': 'sender1gmail.com',
            'password': 'password'
        },
        {
            'email': 'sender2gmail.com',
            'password': 'password',
            'quota': {
                'messages': 900,
                'messages_at_once': 50,
                'seconds_interval': 600}
        }
    ]

    Recipients file example recipients.json
    [
        'recipient1.@gmail.com',
        'recipient2.@gmail.com',
    ]
    '''

    recipients = json.loads(open('recipients.json', 'r').read())
    senders = list()
    for sender_dict in json.loads(open('senders.json', 'r').read()):
        senders.append(load_account(sender_dict))
    do_sending_messages(senders, recipients, 'Hello', SMTPResolver())


if __name__ == '__main__':
    try:
        configure_logger()
        main()
    except KeyboardInterrupt:
        logging.critical('Interrupted')
    except BaseException as e:
        logging.critical(f"Critical error. {e}")
