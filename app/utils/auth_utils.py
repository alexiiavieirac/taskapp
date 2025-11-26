import re

def validar_senha(senha):
    # Verifica se a senha atende aos requisitos
    # Regex combinada para garantir todos os requisitos em uma única verificação
    # (8 a 15 caracteres, pelo menos uma maiúscula, uma minúscula, um número, um caractere especial)
    # ^                 # Início da string
    # (?=.*[a-z])       # Deve conter pelo menos uma letra minúscula
    # (?=.*[A-Z])       # Deve conter pelo menos uma letra maiúscula
    # (?=.*\d)          # Deve conter pelo menos um dígito
    # (?=.*[!@#$%^&*(),.?":{}|<>]) # Deve conter pelo menos um caractere especial
    # [A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,15} # Permite apenas os caracteres especificados e define o comprimento
    # $                 # Fim da string
    senha_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])[A-Za-z\d!@#$%^&*(),.?\":{}|<>]{8,15}$"
    return re.fullmatch(senha_regex, senha) is not None