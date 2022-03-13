import re


def is_password(password: str) -> bool:
    return bool(re.match(r'^[\S]+$', password))


def get_email_prefix(email: str) -> str:
    matcher = re.search(r'^.+@', email)
    assert matcher is not None,\
        f"Cannot get prefix for email '{email}'"
    return matcher.group(0)[0:-1]


def get_email_suffix(email: str) -> str:
    matcher = re.search(r'@.+$', email)
    assert matcher is not None,\
        f"Cannot get suffix for email '{email}'"
    return matcher.group(0)[1:]


def is_email_address(email: str) -> bool:
    return bool(re.match(r'^([^.]+.)*[^.]+@([^.]+.)*[^.]+$', email))


def is_hostname(hostname: str) -> bool:
    return bool(re.match(r'^([^.]+.)*[^.]+$', hostname))


def is_email_prefix(email: str) -> bool:
    return is_hostname(email)


def is_email_suffix(email: str) -> bool:
    return is_hostname(email)


def is_file_path(path: str) -> bool:
    return bool(re.match(r'^(\S+/|\\)*\S+$', path))
