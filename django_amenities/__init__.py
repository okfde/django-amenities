__version__ = '0.0.3'


class Registry():
    def __init__(self):
        self.users = []

    def register(self, user):
        self.users.append(user)

    def iter_users(self, method_name, *args):
        for user in self.users:
            method = getattr(user, method_name, None)
            if method is not None:
                yield method(*args)


registry = Registry()
