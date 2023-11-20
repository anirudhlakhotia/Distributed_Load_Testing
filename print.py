class PrintStyles:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def print_header(message):
    print(f"{PrintStyles.HEADER}{message}{PrintStyles.ENDC}")

def print_success(message):
    print(f"{PrintStyles.OKGREEN}{message}{PrintStyles.ENDC}")

def print_warning(message):
    print(f"{PrintStyles.WARNING}{message}{PrintStyles.ENDC}")

def print_error(message):
    print(f"{PrintStyles.FAIL}{message}{PrintStyles.ENDC}")
