from os import getenv
from pathlib import Path


__all__ = ["Config"]


DEFAULT_VALUES = {
    "SET_WEBHOOK": False,
    "INTERNAL_HOST": "127.0.0.1",
    "DATABASE_HOST": "127.0.0.1",
    "DATABASE_PORT": 6379,
    "DATABASE_NAME": "nftgram",
    "SKIP_UPDATES": False,
    "UPLOADS_DIRECTORY": Path(__file__).parents[1] / "uploads",
}


def get_typed_env(key):
    """Get an environment variable with inferred type."""
    env = getenv(key)
    if env is None:
        return None
    elif env == "true":
        return True
    elif env == "false":
        return False
    try:
        return int(env)
    except ValueError:
        return env


class Config:
    """Lazy interface to configuration values."""

    def __setattr__(self, name, value):
        """Set configuration value."""
        super().__setattr__(name, value)

    def __getattr__(self, name):
        """Get configuration value.

        Return value of environment variable ``name`` if it is set or
        default value otherwise.
        """
        env = get_typed_env(name)
        if env is not None:
            value = env
        elif name not in DEFAULT_VALUES:
            raise AttributeError(f"config has no option '{name}'")
        else:
            value = DEFAULT_VALUES[name]
        setattr(self, name, value)
        return value
