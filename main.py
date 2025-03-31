import logging
import os
from io import BytesIO

from fastapi import Response
from fastapi.responses import StreamingResponse
from chainlit.server import app as chainlit_app

def get_env_var(var_name: str) -> str:
    """Retrieve required environment variable or raise error."""
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"{var_name} is not set.")
    return value

import app

# ASGI entry point
app = chainlit_app
