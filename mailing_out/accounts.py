from service.operations import is_email_address, is_password


class SenderQuota:
    def __init__(self, messages: int = 100,
                 messages_at_once: int = 100,
                 seconds_interval: float = 86400):
        self.__messages = 100
        self.__messages_at_once = 100
        self.__seconds_interval = 86400
        self.messages = messages
        self.messages_at_once = messages_at_once
        self.seconds_interval = seconds_interval

    @property
    def messages(self) -> int:
        return self.__messages

    @messages.setter
    def messages(self, value: int):
        assert value > 0, 'Messages amount to send must be positive'
        self.__messages = value

    @property
    def messages_at_once(self) -> int:
        return self.__messages

    @messages_at_once.setter
    def messages_at_once(self, value: int):
        assert value > 0, 'Messages amount at once ' \
                          'to send must be positive'
        self.__messages_at_once = value

    @property
    def seconds_interval(self):
        return self.__seconds_interval

    @seconds_interval.setter
    def seconds_interval(self, interval: float):
        assert interval >= 0, 'Account quota interval must be positive'
        self.__seconds_interval = interval

    def __str__(self):
        return f"{self.messages} messages," \
               f"{self.messages_at_once} at once," \
               f"{self.seconds_interval} seconds interval"

    def __repr__(self):
        return f"{type(self).__module__}." \
               f"{type(self).__name__}({self.messages}, " \
               f"{self.messages_at_once}, " \
               f"{self.seconds_interval})"


class SenderAccount:
    def __init__(self, email: str = 'norepry@unknown',
                 password: str = 'password'):
        self.__email = str()
        self.__password = str()
        self.__quota = SenderQuota()
        self.email = email
        self.password = password

    @property
    def email(self):
        return self.__email

    @email.setter
    def email(self, email: str):
        assert is_email_address(email),\
            f"Invalid email format '{email}'"
        self.__email = email

    @property
    def password(self) -> str:
        return self.__password

    @password.setter
    def password(self, password: str):
        assert is_password(password),\
            f"Invalid password format '{password}'"
        self.__password = password

    @property
    def quota(self) -> SenderQuota:
        return self.__quota

    @quota.setter
    def quota(self, quota: SenderQuota):
        self.__quota = quota

    def __str__(self):
        return self.email

    def __repr__(self):
        return f"{type(self).__module__}." \
               f"{type(self).__name__}({self.email}, " \
               f"{self.password}, " \
               f"{repr(self.quota)})"
