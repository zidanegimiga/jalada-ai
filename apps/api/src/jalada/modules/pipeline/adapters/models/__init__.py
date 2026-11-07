"""Language model adapters. Importing this package registers every provider adapter, so
the registry can build any model in the catalogue."""

from jalada.modules.pipeline.adapters.models import gemini, ollama, openai_compatible

__all__ = ["gemini", "ollama", "openai_compatible"]
