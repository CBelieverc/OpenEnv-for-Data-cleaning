"""FastAPI application for the Data Cleaning Environment."""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required. Install with: pip install openenv-core[core]"
    ) from e

try:
    from ..models import CleanAction, CleaningObservation
    from .data_cleaning_env_environment import DataCleaningEnvironment
except (ModuleNotFoundError, ImportError):
    from models import CleanAction, CleaningObservation
    from server.data_cleaning_env_environment import DataCleaningEnvironment

app = create_app(
    DataCleaningEnvironment,
    CleanAction,
    CleaningObservation,
    env_name="data_cleaning_env",
    max_concurrent_envs=10,
)


def main(host: str = "0.0.0.0", port: int = 8000):
    """Entry point for running the server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
