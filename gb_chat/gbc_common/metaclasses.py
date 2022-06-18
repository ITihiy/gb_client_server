import dis


class ServerVerifier(type):
    def __init__(cls, cls_name, cls_base, cls_dict):
        opname_dict = {'LOAD_GLOBAL': [], 'LOAD_METHOD': [], 'LOAD_ATTR': []}
        for func in cls_dict:
            try:
                res = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for current_func in res:
                    if current_func.opname in opname_dict:
                        opname_dict[current_func.opname].append(current_func.argval)
        if 'connect' in opname_dict['LOAD_METHOD']:
            raise TypeError('Incorrect use of "connect" in Server class')
        if 'AF_INET' not in opname_dict['LOAD_ATTR'] or 'SOCK_STREAM' not in opname_dict['LOAD_ATTR']:
            raise TypeError('TCP socket for server expected')
        super().__init__(cls_name, cls_base, cls_dict)


class ClientVerifier(type):
    def __init__(cls, cls_name, cls_base, cls_dict):
        opname_dict = {'LOAD_METHOD': [], 'LOAD_ATTR': []}
        for func in cls_dict:
            try:
                res = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for current_func in res:
                    if current_func.opname in opname_dict:
                        opname_dict[current_func.opname].append(current_func.argval)
        if any(func in opname_dict['LOAD_METHOD'] for func in ['listen', 'accept']):
            raise TypeError('Incorrect use of function in client')
        if 'AF_INET' not in opname_dict['LOAD_ATTR'] or 'SOCK_STREAM' not in opname_dict['LOAD_ATTR']:
            raise TypeError('TCP socket for server expected')
        super().__init__(cls_name, cls_base, cls_dict)
