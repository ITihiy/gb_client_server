from gbc_common.variables import DEFAULT_SERVER_PORT


class PortDescriptor:
    def __set_name__(self, owner, name):
        self.attr_name = name

    def __set__(self, instance, value):
        if value < 1024 or value > 65535:
            raise ValueError(f'Incorrect port number {value}. Should be in range (1024-65535)')
        instance.attr_name = value

    def __get__(self, instance, owner):
        return DEFAULT_SERVER_PORT if not instance.attr_name else instance.attr_name
