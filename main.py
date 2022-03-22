import logging
import random
from argparse import ArgumentParser, Namespace
from logging import StreamHandler, Formatter
import sys
from datetime import datetime
import json
from smtplib import SMTPException

from mailing_out.parser import load_account, load_quota_resolver
from mailing_out.messages import EmailMessage
from service.exceptions import WithResultException
from service.operations import get_email_suffix, is_file_path, is_email_address
from mailing_out.resolvers import DefaultQuotaResolver, DefaultSMTPResolver, SMTPResolver


def configure_logger():
    handler = StreamHandler(stream=sys.stdout)
    handler.setFormatter(Formatter(
        fmt='[%(asctime)s: %(levelname)s] %(message)s'))
    logging.basicConfig(level='DEBUG', handlers=[handler])


def assert_file_path(path: str, parameter: str):
    assert is_file_path(path), f"{parameter} path has invalid format" \
                               f" '{path}'"


def read_file_bytes(path: str) -> bytes:
    return open(path, 'rb').read()


def read_file_content(path: str, encoding: str = 'utf-8') -> str:
    return read_file_bytes(path).decode(encoding)


def write_file_content(path: str, content: str):
    open(path, 'w').write(content)


def create_message(attachments: dict, html: str = None,
                   subject: str = None,
                   sender: str = None) -> EmailMessage:
    message = EmailMessage()
    if sender is not None:
        message.set_header('From', sender)
    if subject is not None:
        message.set_header('Subject', subject)
    if html is not None:
        message.set_content('html', html)
    for name in attachments.keys():
        message.set_attachment(name, attachments[name])
    return message


def initialize_arguments() -> Namespace:
    arg_parser = ArgumentParser(
        prog='furry-funicular',
        description='Mass mailing program ')
    arg_parser.add_argument(
        '-s',
        metavar='file',
        type=str,
        required=True,
        help='senders json file path')
    arg_parser.add_argument(
        '-r',
        metavar='file',
        type=str,
        required=True,
        help='recipients json file path')
    arg_parser.add_argument(
        '-t',
        metavar='subject',
        type=str,
        default=None,
        help="message subject ('Subject' header)")
    arg_parser.add_argument(
        '-w',
        metavar='file',
        type=str,
        default=None,
        help='message html file path')
    arg_parser.add_argument(
        '-e',
        metavar='email',
        type=str,
        default=None,
        help="message sender email ('From' header). By default "
             "for every sender uses its own address")
    arg_parser.add_argument(
        '-a',
        metavar=('name', 'path'),
        type=str,
        nargs=2,
        default=list(),
        action='append',
        help='message attachment name and file path')
    arg_parser.add_argument(
        '-m',
        metavar='amount',
        type=int,
        default=None,
        help='messages limit amount. By default has no limit (when '
             'the message was sent to all recipients from the file,'
             ' sending starts again)')
    arg_parser.add_argument(
        '-f',
        metavar='file',
        type=str,
        default=None,
        help='output json file for recipients that did not received '
             'message. Remaining recipients are not recorded by'
             'default')
    arg_parser.add_argument(
        '-o',
        type=str,
        metavar='order',
        choices={'asc', 'desc', 'rand'},
        default='asc',
        help="recipients order: 'asc', 'desc', 'rand'. By default 'asc'")
    arg_parser.add_argument(
        '-q',
        type=str,
        metavar='file',
        default='quota-resolver.json',
        help="quota resolver json file path. Default value"
             " 'quota-resolver.json'")
    params = arg_parser.parse_args()
    assert_file_path(params.s, 'Senders file')
    assert_file_path(params.r, 'Recipients file')
    if params.w is not None:
        assert_file_path(params.s, 'Message html file')
    for attach_params in params.a:
        assert_file_path(attach_params[0], 'Message attachment file')
    if params.m is not None:
        assert params.m > 0, f"Invalid amount of messages {params.m}"
    if params.f is not None:
        assert_file_path(params.f, 'Output recipients file')
    assert_file_path(params.q, 'Quota resolver file')
    if params.e is not None:
        assert is_email_address(params.e), f"Invalid sender email" \
                                       f"format '{params.e}'"
    return params


def do_sending_messages(senders: list, recipients: list,
                        message: EmailMessage,
                        client_resolver: SMTPResolver,
                        senders_in_message: bool,
                        messages_amount: int = None,
                        summary_interval: float = 20):
    assert len(senders) > 0, "There are no senders to send messages"
    assert len(recipients) > 0, "There are no recipients for " \
                                "receiving messages"

    send_labels = dict()
    time_label = datetime.now().timestamp()
    summary_time_label = datetime.now().timestamp()
    position = 0
    for sender in senders:
        send_labels[sender] = time_label - sender.quota.\
            seconds_interval
    summary_sent = 0
    try:
        while (messages_amount is None or
               summary_sent < messages_amount):
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
                        if senders_in_message:
                            message.set_header('From', sender.email)
                        message.set_header('To', ','.join(rec_at_once))
                        client.send_mail(rec_at_once,
                                         message.as_string())
                        summary_sent += at_once
                        position += at_once
                        if position >= len(recipients):
                            logging.info(f"Messages was sent to all "
                                         f"{len(recipients)}"
                                         f"recipients")
                            position = 0
                        sent_by_sender += at_once
                except SMTPException as e:
                    logging.info(f"Sending message error at sender '"
                                 f"{sender}'. Error data {e.args}")
                finally:
                    client.disconnect()
                    send_labels[sender] = datetime.now().timestamp()
    except BaseException as e:
        wrapper = WithResultException(e)
        recipients_left = list()
        if summary_sent < len(recipients):
            recipients_left = recipients[position:]
        wrapper.result = recipients_left
        raise wrapper


def main():
    configure_logger()
    params = initialize_arguments()

    quota_resolver = DefaultQuotaResolver()
    try:
        quota_resolver = load_quota_resolver(json.loads(
            read_file_content(params.q)))
    except IOError as e:
        logging.warning(f"Quota resolver file reading error. {e}")

    recipients = json.loads(read_file_content(params.r))
    assert type(recipients) == list, "Invalid recipients json file"
    for recipient in recipients:
        assert type(recipient) == str, "Invalid recipients json file"
        assert is_email_address(recipient),\
            f"Invalid recipient email address '{recipient}'"

    senders = list()
    for sender_dict in json.loads(read_file_content(params.s)):
        senders.append(load_account(sender_dict, quota_resolver))

    attachments = dict()
    for attach_params in params.a:
        attachments[attach_params[0]] =\
            read_file_bytes(attach_params[1])

    if params.o == 'rand':
        random.shuffle(recipients)
    elif params.o == 'desc':
        recipients.reverse()

    html_content = None
    if params.w is not None:
        html_content = read_file_content(params.w)

    message = create_message(attachments, html_content, params.t,
                             params.e)
    try:
        do_sending_messages(senders, recipients, message,
                            DefaultSMTPResolver(), params.e is None,
                            params.m)
    except WithResultException as e:
        if params.f is not None:
            write_file_content(params.f, json.dumps(e.result))
            logging.info(f"Left recipients saved into file "
                         f"'{params.f}'")
        raise e.root_cause


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        pass
    except KeyboardInterrupt:
        logging.critical('Interrupted')
    except BaseException as e:
        logging.critical(f"Critical error. {e}")
