"""Builds a model from its profile with the adapter registered for its provider.

Each adapter registers itself with @provider("name"). Supporting a new kind of provider
means adding one adapter module and importing it in this package's __init__; nothing that
uses models changes. Most hosted models need no new adapter at all: openai_compatible
reaches any provider that speaks the OpenAI chat completions API.
"""

from collections.abc import Callable

from jalada.modules.pipeline.adapters.models.profiles import ModelProfile, ProviderAccount
from jalada.modules.pipeline.domain.model import LanguageModel

ProviderFactory = Callable[[ModelProfile, ProviderAccount], LanguageModel]
PROVIDERS: dict[str, ProviderFactory] = {}


class ModelSetupError(ValueError):
    """The model settings cannot work. Raised at startup, so a bad deploy fails fast."""


def provider(name: str) -> Callable[[ProviderFactory], ProviderFactory]:
    def register(factory: ProviderFactory) -> ProviderFactory:
        PROVIDERS[name] = factory
        return factory

    return register


def build_model(profile: ModelProfile, accounts: dict[str, ProviderAccount]) -> LanguageModel:
    factory = PROVIDERS.get(profile.provider)
    if factory is None:
        known = ", ".join(sorted(PROVIDERS))
        raise ModelSetupError(f"{profile.name}: unknown provider {profile.provider!r} ({known})")
    account = accounts.get(profile.account)
    if account is None:
        raise ModelSetupError(
            f"{profile.name}: add a {profile.account!r} entry to JALADA_MODEL_PROVIDERS"
        )
    return factory(profile, account)
