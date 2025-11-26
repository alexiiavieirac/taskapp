from urllib.parse import urljoin, urlparse
from flask import request


def is_safe_url(target):
    # Impede redirecionamento externo malicioso
    # Garantir que a URL de destino esteja no mesmo domínio da aplicação para segurança
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    # Verifica se o esquema é HTTP ou HTTPS E se o netloc (domínio:porta) é o mesmo.
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc