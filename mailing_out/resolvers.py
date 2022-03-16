from mailing_out.accounts import SenderQuota
from mailing_out.smtp.clients import SMTPClient
from service.operations import is_email_suffix


class SMTPResolver:
    def __init__(self):
        self.__clients = dict()

    def add_client(self, suffix: str, client: SMTPClient):
        self.__clients[suffix] = client

    def remove_client(self, suffix):
        self.__clients.pop(suffix)

    def clear_clients(self):
        self.__clients = dict()

    def get_client(self, email_suffix: str) -> SMTPClient:
        client = self.__clients.get(email_suffix)
        if client is None:
            client = SMTPClient('smtp.' + email_suffix, 465)
        return client


class QuotaResolver:
    def __init__(self):
        self.__quotas = dict()
        self.__default_quota = SenderQuota(100, 100, 60)

    @property
    def default_quota(self):
        return self.__default_quota

    @default_quota.setter
    def default_quota(self, quota: SenderQuota):
        self.__default_quota = quota

    def add_quota(self, suffix: str, quota: SenderQuota):
        assert is_email_suffix(suffix),\
            f"Email suffix has invalid format '{suffix}'"
        self.__quotas[suffix] = quota

    def remove_quota(self, suffix: str):
        assert is_email_suffix(suffix),\
            f"Email suffix has invalid format '{suffix}'"
        self.__quotas.pop(suffix)

    def get_suffixes(self):
        return self.__quotas.keys()

    def clear_quotas(self):
        self.__quotas.clear()

    def get_quota(self, email_suffix: str) -> SenderQuota:
        quota = self.__quotas.get(email_suffix)
        if quota is None:
            quota = self.__default_quota
        return quota


class DefaultSMTPResolver(SMTPResolver):
    def __init__(self):
        super().__init__()
        self.add_client(
            'yahoo.com',
            SMTPClient('smtp.mail.yahoo.com'))
        self.add_client(
            'hotmail.com',
            SMTPClient('smtp.mail-outlook.com'))
        self.add_client(
            'tut.by',
            SMTPClient('smtp.mail.tut.by'))
        mail_ru_client = SMTPClient('smtp.mail.ru')
        self.add_client('mail.ru', mail_ru_client)
        self.add_client('list.ru', mail_ru_client)
        self.add_client('inbox.ru', mail_ru_client)


class DefaultQuotaResolver(QuotaResolver):
    def __init__(self):
        super().__init__()
        self.add_quota('gmail.com', SenderQuota(500, 100))
        self.add_quota('yahoo.com', SenderQuota(100, 100, 3600))
        self.add_quota('hotmail.com', SenderQuota(300, 300))
        self.add_quota('yandex.ru', SenderQuota(150, 25))
        self.add_quota('tut.by', SenderQuota(500, 100))
        self.add_quota('rambler.ru', SenderQuota(200, 200))
        self.add_quota('ukr.net', SenderQuota(250, 250))
        self.add_quota('meta.ua', SenderQuota(200, 200))
        self.add_quota('aol.com', SenderQuota(500, 500))
        self.add_quota('lycos.com', SenderQuota(250, 250))
        self.default_quota = SenderQuota(100, 100, 60)
