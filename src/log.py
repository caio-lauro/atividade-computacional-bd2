def log_info(*args):
    INFO = "     \033[48;2;0;113;102m INFO \033[0m "
    print(INFO, *args)


def log_error(*args):
    ERROR = "     \033[48;2;197;15;52m ERRO \033[0m "
    print(ERROR, *args)
