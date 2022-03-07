import smtplib

from service.operations import is_hostname
from smtp.accounts import SenderAccount


class SMTPClient:
    def __init__(self, host: str, port: int):
        self.__smtp_host = str()
        self.__smtp_port = int()
        self.smtp_host = host
        self.smtp_port = port

    @property
    def smtp_host(self) -> str:
        return self.__smtp_host

    @smtp_host.setter
    def smtp_host(self, host: str):
        assert is_hostname(host), f"Invalid SMTP hostname '{host}'"
        self.__smtp_host = host

    @property
    def smtp_port(self) -> int:
        return self.__smtp_port

    @smtp_port.setter
    def smtp_port(self, port: int):
        assert 0 <= port <= 65535, f"Invalid SMTP port value '{port}'"
        self.__smtp_port = port

    def send_one(self, sender: SenderAccount, recipients: list,
                 message: str):
        server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        server.login(sender.email, sender.password)
        server.sendmail(sender.email,
                        recipients, message)
        server.quit()

    def send_multiple(self, sender: SenderAccount, recipients: list,
                      message: str):
        at_once = sender.quota.messages_at_once
        position = 0
        while position < len(recipients):
            rec_at_once = recipients[position:position + at_once]
            self.send_one(sender, rec_at_once, message)
            position += at_once
