import json

from service.operations import get_email_suffix
from smtp.parser import loads_account
from smtp.resolvers import SMTPResolver


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
                'messages_at_once': 50}
        }
    ]

    Recipients file example recipients.json
    [
        'recipient1.@gmail.com',
        'recipient2.@gmail.com',
    ]
    '''

    recipients = json.loads(open('recipients.json', 'r').read())

    for account_dict in json.loads(open('senders.json', 'r').read()):
        account = loads_account(account_dict)
        client = SMTPResolver().get_client(get_email_suffix(account.email))
        client.send_multiple(account, recipients, 'Hello')


if __name__ == '__main__':
    main()
