from datetime import datetime
import json

from service.operations import get_email_suffix
from smtp.parser import loads_account
from smtp.resolvers import SMTPResolver


def do_sending_messages(senders: list, recipients: list,
                        message: str, client_resolver: SMTPResolver,
                        messages_amount: int = None):
    send_labels = dict()
    time_label = datetime.now().timestamp()
    position = 0
    for sender in senders:
        send_labels[sender] = time_label - sender.quota.\
            seconds_interval * 1000
    summary_sent = 0
    while messages_amount is None or summary_sent < messages_amount:
        for sender in senders:
            interval = sender.quota.seconds_interval
            at_once = sender.quota.messages_at_once
            messages = sender.quota.messages
            if datetime.now().timestamp() - send_labels[
                sender] < interval * 1000:
                continue
            client = client_resolver.get_client(get_email_suffix(
                sender.email))
            sent_by_sender = 0
            try:
                while sent_by_sender < messages:
                    if position + at_once > messages:
                        at_once = messages - position - 1
                    rec_at_once = recipients[
                                  position:position + at_once]
                    client.send_one(sender, rec_at_once, message)
                    summary_sent += at_once
                    position += at_once
                    sent_by_sender += at_once
            finally:
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
        senders.append(loads_account(sender_dict))
    do_sending_messages(senders, recipients, 'Hello', SMTPResolver(), 1)


if __name__ == '__main__':
    main()
