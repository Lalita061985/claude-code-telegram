import logging

from src.main import setup_logging


def test_http_clients_never_log_token_bearing_request_urls() -> None:
    setup_logging(debug=True)

    assert logging.getLogger("httpx").getEffectiveLevel() >= logging.WARNING
    assert logging.getLogger("httpcore").getEffectiveLevel() >= logging.WARNING
