import logging
import random
from argparse import ArgumentParser, Namespace
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import StreamHandler, Formatter
import sys
from datetime import datetime
import json
from smtplib import SMTPException

from mailing_out.parser import load_account
from service.operations import get_email_suffix, is_file_path, is_email_address
from mailing_out.resolvers import SMTPResolver


def configure_logger():
    handler = StreamHandler(stream=sys.stdout)
    handler.setFormatter(Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
    logging.basicConfig(level='INFO', handlers=[handler])


def create_message(attachments: dict, html: str = None,
                   subject: str = None) -> str:
    message = MIMEMultipart('alternative')
    if subject is not None:
        message['Subject'] = subject
    if html is not None:
        html_part = MIMEText(html, 'html')
        message.attach(html_part)
    for name in attachments.keys():
        attachment_part = MIMEBase('application', 'octet-stream')
        attachment_part.set_payload(attachments[name])
        encode_base64(attachment_part)
        attachment_part.add_header('Content-Disposition',
                                   f"attachment; filename={name}")
        message.attach(attachment_part)
    return message.as_string()


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
        help='message subject')
    arg_parser.add_argument(
        '-w',
        metavar='file',
        type=str,
        default=None,
        help='message html file path')
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
        help='messages limit amount. By default has no limit')
    arg_parser.add_argument(
        '-o',
        type=str,
        choices={'asc', 'desc', 'rand'},
        default='asc',
        help="recipients order: 'asc', 'desc', 'rand'")
    params = arg_parser.parse_args()
    assert is_file_path(params.s), f"Invalid senders file " \
                                   f"path format {params.s}"
    assert is_file_path(params.r), f"Invalid recipients file " \
                                   f"path format {params.r}"
    if params.w is not None:
        assert is_file_path(params.w), f"Invalid html file " \
                                       f"path format {params.w}"
    for attach_params in params.a:
        assert is_file_path(attach_params[0]),\
            f"Invalid attachment file path format {params.s}"
    if params.m is not None:
        assert params.m > 0, f"Invalid amount of messages {params.m}"
    return params


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
    configure_logger()
    params = initialize_arguments()
    recipients = json.loads(open(params.r, 'r').read())
    assert type(recipients) == list, "Invalid recipients json file"
    for recipient in recipients:
        assert type(recipient) == str, "Invalid recipients json file"
        assert is_email_address(recipient),\
            f"Invalid recipient email address '{recipient}'"
    if params.o == 'rand':
        random.shuffle(recipients)
    elif params.o == 'desc':
        recipients.reverse()
    senders = list()
    for sender_dict in json.loads(open(params.s, 'r').read()):
        senders.append(load_account(sender_dict))
    attachments = dict()
    for attach_params in params.a:
        attachments[attach_params[0]] =\
            open(attach_params[1], 'rb').read()
    message = create_message(attachments, params.w, params.t)
    do_sending_messages(senders, recipients, message,
                        SMTPResolver(), params.m)


if __name__ == '__main__':
    try:
        main()
    except SystemExit as e:
        pass
    except KeyboardInterrupt:
        logging.critical('Interrupted')
    except BaseException as e:
        logging.critical(f"Critical error. {e}")
