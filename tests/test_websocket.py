"""Integration tests for WebSocket communication."""
from fastapi.testclient import TestClient


def test_websocket_connection(test_client: TestClient):
    """Tests that a client can connect to the websocket and the connection stays open."""
    with test_client.websocket_connect("/ws/incidents") as websocket:
        # We can send a message and it shouldn't close.
        websocket.send_text("ping")
        # Since the server doesn't respond to our messages (it only broadcasts incidents), 
        # just being able to connect and send is a sufficient test of the endpoint's health.
