import random

from app.core.config import ProviderAccount, get_settings
from app.providers.base import BaseSerpProvider
from app.providers.serper.client import SerperProvider
from app.providers.serpbase.client import SerpBaseProvider


PROVIDER_CLASSES: dict[str, type[BaseSerpProvider]] = {
    "serpbase": SerpBaseProvider,
    "serper": SerperProvider,
}


def get_provider_account(account_name: str | None = None) -> ProviderAccount:
    settings = get_settings()
    selected_name = account_name or settings.default_provider_account

    if selected_name:
        if selected_name not in settings.provider_accounts:
            raise ValueError(f"Unknown provider account: {selected_name}")
        account = settings.provider_accounts[selected_name]
        if not account.enabled:
            raise ValueError(f"Provider account is disabled: {selected_name}")
        return account

    enabled_accounts = [account for account in settings.provider_accounts.values() if account.enabled]
    if not enabled_accounts:
        raise ValueError("No enabled provider accounts available")
    return random.choice(enabled_accounts)


def build_provider(account_name: str | None = None) -> BaseSerpProvider:
    account = get_provider_account(account_name)
    provider_class = PROVIDER_CLASSES.get(account.provider)
    if provider_class is None:
        raise ValueError(f"Unsupported provider: {account.provider}")
    return provider_class(account)
