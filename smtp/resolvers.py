from smtp.accounts import SenderQuota
from smtp.clients import SMTPClient


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
            return SenderQuota(400, 100)
        else:
            return SenderQuota(100, 100)
