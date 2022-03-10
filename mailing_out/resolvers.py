from mailing_out.accounts import SenderQuota
from mailing_out.smtp.clients import SMTPClient


class SMTPResolver:
    def __init__(self):
        self._clients = dict()

    def add_client(self, suffix: str, client: SMTPClient):
        self._clients[suffix] = client

    def remove_client(self, suffix):
        self._clients.pop(suffix)

    def clear_clients(self):
        self._clients = dict()

    def get_client(self, email_suffix: str) -> SMTPClient:
        client = self._clients.get(email_suffix)
        if client is None:
            client = SMTPClient('smtp.' + email_suffix, 465)
        return client


class SenderQuotaFactory:
    def get_quota(self, email_suffix: str) -> SenderQuota:
        if email_suffix == 'gmail.com':
            return SenderQuota(500, 100)
        elif email_suffix == 'yahoo.com':
            return SenderQuota(100, 100, 3600)
        elif email_suffix == 'hotmail.com':
            return SenderQuota(300, 300)
        elif email_suffix == 'yandex.ru':
            return SenderQuota(150, 25)
        elif email_suffix == 'tut.by':
            return SenderQuota(500, 100)
        elif email_suffix == 'rambler.ru':
            return SenderQuota(200, 200)
        elif email_suffix == 'ukr.net':
            return SenderQuota(250, 250)
        elif email_suffix == 'meta.ua':
            return SenderQuota(200, 200)
        elif email_suffix == 'aol.com':
            return SenderQuota(500, 500)
        elif email_suffix == 'lycos.com':
            return SenderQuota(250, 250)
        else:
            return SenderQuota(100, 100)
