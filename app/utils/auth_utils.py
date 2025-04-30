import re

def validar_senha(senha):
    # Verifica se a senha atende aos requisitos
    if len(senha) < 8 or len(senha) > 15:
        return False
    if not re.search(r"[A-Z]", senha):  # Verifica se tem letra maiúscula
        return False
    if not re.search(r"[0-9]", senha):  # Verifica se tem número
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", senha):  # Verifica se tem caractere especial
        return False
    return True