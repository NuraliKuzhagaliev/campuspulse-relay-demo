import time
import pytest
from cryptography.fernet import Fernet
from relay.oauth import credentials,configuration
from relay.store import Store
from relay.domain import RelayError
from relay.limits import consume


def test_unconfigured_auth_is_explicit(monkeypatch):
    monkeypatch.delenv('RELAY_OAUTH_CLIENT_ID',raising=False)
    with pytest.raises(RelayError,match='RELAY_OAUTH_CLIENT_ID'):
        configuration()


def test_no_token_fallback_or_cross_tenant(tmp_path,monkeypatch):
    store=Store(tmp_path/'auth.db');monkeypatch.setenv('RELAY_TOKEN_ENCRYPTION_KEY',Fernet.generate_key().decode())
    store.put('a','private_connections','google',{'ciphertext':'not-a-valid-cipher'})
    for tenant in ('a','b'):
        with pytest.raises(RelayError,match='Connect Google'):
            credentials(store,tenant)


def test_durable_request_budget_and_tenant_scoping(tmp_path):
    path=tmp_path/'limits.db';store=Store(path)
    consume(store,'a','minute',60,1)
    with pytest.raises(RelayError,match='allowance'):
        consume(Store(path),'a','minute',60,1)
    consume(store,'b','minute',60,1)
