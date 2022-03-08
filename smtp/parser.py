from service.operations import get_email_suffix
from smtp.accounts import SenderAccount, SenderQuota
from smtp.resolvers import SenderQuotaFactory


def loads_account(value: dict,
                  quota_resolver: SenderQuotaFactory =
                  SenderQuotaFactory()) -> SenderAccount:
    assert value.get('email') is not None,\
        'Required email value for sender account'
    assert value.get('password') is not None,\
        f"Required password value for sender account {value['email']}"
    account = SenderAccount(value['email'], value['password'])
    account.quota = quota_resolver.get_quota(
        get_email_suffix(account.email))
    quota_dict = value.get('quota')
    if quota_dict is not None:
        account.quota = loads_quota(quota_dict)
    return account


def dumps_account(account: SenderAccount) -> dict:
    return {
        'email': account.email,
        'password': account.password,
        'quota': dumps_quota(account.quota)
    }


def loads_quota(value: dict) -> SenderQuota:
    assert value.get('messages'),\
        'Required messages amount for sender quota'
    assert value.get('messages-at-once'),\
        'Required messages at once amount for sender quota'
    return SenderQuota(value['messages'], value['messages-at-once'])


def dumps_quota(quota: SenderQuota) -> dict:
    return {
        'messages': quota.messages,
        'messages-at-once': quota.messages_at_once
    }
