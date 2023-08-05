from collections import namedtuple
from unittest import mock

import pytest_asyncio

import app
from approaches.approach import Approach
from approaches.chatreadretrieveread import ChatReadRetrieveReadApproach


class MockedAskApproach(Approach):
    async def run(self, question, overrides):
        assert question == "What is the capital of France?"
        return {"answer": "Paris"}


class MockedChatApproach(ChatReadRetrieveReadApproach):
    def __init__(self):
        pass

    async def run(self, history, overrides):
        messages = ChatReadRetrieveReadApproach.get_messages_from_history(self, ChatReadRetrieveReadApproach.query_prompt_template, "gpt-3.5-turbo", history, "Generate search query")
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Generate search query"
        assert messages[1]["role"] == "user"
        return {"answer": "Paris", "data_points": [], "thoughts": ""}


MockToken = namedtuple("MockToken", ["token", "expires_on"])


class MockAzureCredential:
    async def get_token(self, uri):
        return MockToken("mock_token", 9999999999)


@pytest_asyncio.fixture
async def client():
    # mock the DefaultAzureCredential
    with mock.patch("app.DefaultAzureCredential") as mock_default_azure_credential:
        mock_default_azure_credential.return_value = MockAzureCredential()
        quart_app = app.create_app()

        async with quart_app.test_app() as test_app:
            quart_app.config.update(
                {
                    "TESTING": True,
                    app.CONFIG_ASK_APPROACHES: {"mock": MockedAskApproach()},
                    app.CONFIG_CHAT_APPROACHES: {"mock": MockedChatApproach()},
                }
            )

            yield test_app.test_client()
