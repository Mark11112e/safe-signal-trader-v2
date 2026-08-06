"""Signal source registry – stable source_id + parser/profile binding."""
from signal_bot.sources.models import SourceConfig
from signal_bot.sources.registry import SourceRegistry, build_example_registry

__all__ = ["SourceConfig", "SourceRegistry", "build_example_registry"]
