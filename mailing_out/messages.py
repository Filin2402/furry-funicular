from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailMessage:
    def __init__(self):
        self.__headers = dict()
        self.__attachments = dict()
        self.__contents = dict()

    def set_header(self, name: str, value: str):
        self.__headers[name] = value

    def get_header(self, name) -> str or None:
        return self.__headers.get(name)

    def set_attachment(self, name: str, value: bytes):
        self.__attachments[name] = value

    def get_attachment(self, name: str) -> bytes or None:
        return self.__attachments.get(name)

    def set_content(self, content_type: str, text: str):
        self.__contents[content_type] = text

    def get_content(self, content_type: str) -> str:
        return self.__contents.get(content_type)

    def as_string(self):
        message = MIMEMultipart('alternative')
        for header_name in self.__headers:
            message[header_name] = self.__headers[header_name]
        for content_type in self.__contents:
            text_part = MIMEText(self.__contents[content_type],
                                 content_type)
            message.attach(text_part)
        for attach_name in self.__attachments:
            attachment_part = MIMEBase('application', 'octet-stream')
            attachment_part.set_payload(
                self.__attachments[attach_name])
            encode_base64(attachment_part)
            attachment_part.add_header(
                'Content-Disposition',
                f"attachment; filename={attach_name}")
            message.attach(attachment_part)
        return message.as_string()
