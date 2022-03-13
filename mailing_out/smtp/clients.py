import logging
import smtplib
from smtplib import SMTPException

from service.operations import is_hostname
from mailing_out.accounts import SenderAccount


class SMTPClient:
    __logger = logging.getLogger(__name__)

    def __init__(self, host: str, port: int = 465):
        self.__smtp_host = str()
        self.__smtp_port = int()
        self.__sender = SenderAccount()
        self.__server = None
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

    @property
    def sender(self) -> SenderAccount:
        return self.__sender

    @sender.setter
    def sender(self, sender: SenderAccount):
        self.__sender = sender

    def connect(self):
        self.__server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        self.__server.login(self.sender.email, self.sender.password)
        self.__logger.debug(f"Connected to '{self.smtp_host}:"
                            f"{self.smtp_port}'")

    def disconnect(self):
        try:
            if self.__server is not None:
                self.__server.quit()
        except SMTPException as e:
            self.__logger.warning(f"Disconnection error. Error data:"
                                  f"'{e}'")
        finally:
            self.__server = None
            self.__logger.debug(f"Disconnected from '{self.smtp_host}:"
                                f"{self.smtp_port}'")

    def send_mail(self, recipients: list, message: str):
        self.__server.sendmail(self.sender.email, recipients, message)
        self.__logger.info(f"Sent messages from '{self.sender}' to"
                           f" {len(recipients)} recipients")
