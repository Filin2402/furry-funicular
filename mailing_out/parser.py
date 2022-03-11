from service.operations import get_email_suffix
from mailing_out.accounts import SenderAccount, SenderQuota
from mailing_out.resolvers import QuotaResolver, DefaultQuotaResolver


def load_account(value: dict,
                 quota_resolver: QuotaResolver =
                 DefaultQuotaResolver()) -> SenderAccount:
    assert value.get('email') is not None,\
        'Required email value for sender account'
    assert value.get('password') is not None,\
        f"Required password value for sender account {value['email']}"
    account = SenderAccount(value['email'], value['password'])
    account.quota = quota_resolver.get_quota(
        get_email_suffix(account.email))
    quota_dict = value.get('quota')
    if quota_dict is not None:
        account.quota = load_quota(quota_dict)
    return account


def dump_account(account: SenderAccount) -> dict:
    return {
        'email': account.email,
        'password': account.password,
        'quota': dump_quota(account.quota)
    }


def load_quota(value: dict) -> SenderQuota:
    assert value.get('messages'),\
        'Required messages amount for sender quota'
    assert value.get('messages-at-once'),\
        'Required messages at once amount for sender quota'
    assert value.get('seconds-interval'),\
        'Required seconds interval for sender quota'
    return SenderQuota(value['messages'],
                       value['messages-at-once'],
                       value['seconds-interval'])


def dump_quota(quota: SenderQuota) -> dict:
    return {
        'messages': quota.messages,
        'messages-at-once': quota.messages_at_once,
        'seconds-interval': quota.seconds_interval
    }


def load_quota_resolver(value: dict) -> QuotaResolver:
    resolver = QuotaResolver()
    for email_suffix in value.keys():
        if email_suffix == 'default':
            resolver.default_quota = load_quota(value[email_suffix])
        else:
            resolver.add_quota(email_suffix,
                               load_quota(value[email_suffix]))
    return resolver


def dump_quota_resolver(resolver: QuotaResolver) -> dict:
    result = dict()
    for email_suffix in resolver.get_suffixes():
        result[email_suffix] = dump_quota(resolver.get_quota(email_suffix))
    result['default'] = resolver.default_quota
    return result
