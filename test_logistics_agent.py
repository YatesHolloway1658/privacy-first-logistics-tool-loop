"""Focused test for the tool-call, tool-result, final-answer sequence."""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from logistics_agent import LogisticsAgent


class LogisticsAgentTest(unittest.TestCase):
    def test_runs_requested_tool_and_returns_final_answer(self) -> None:
        handler = MagicMock(return_value={"status": "ready", "destination_zone": "east-2"})
        agent = LogisticsAgent(api_key="test-key", handlers={"lookup_shipment": handler})
        tool_call = SimpleNamespace(
            id="call-1",
            function=SimpleNamespace(
                name="lookup_shipment",
                arguments=json.dumps({"shipment_id": "SHP-1042"}),
            ),
        )
        first_message = MagicMock(content=None, tool_calls=[tool_call])
        first_message.model_dump.return_value = {
            "role": "assistant",
            "tool_calls": [{"id": "call-1"}],
        }
        final_message = MagicMock(content="Shipment is ready.", tool_calls=None)
        agent._completion = MagicMock(
            side_effect=[
                SimpleNamespace(choices=[SimpleNamespace(message=first_message)]),
                SimpleNamespace(choices=[SimpleNamespace(message=final_message)]),
            ]
        )

        result = agent.run("Check SHP-1042")

        self.assertEqual(result, "Shipment is ready.")
        handler.assert_called_once_with(shipment_id="SHP-1042")
        second_messages = agent._completion.call_args_list[1].args[0]
        self.assertEqual(second_messages[-1]["role"], "tool")
        self.assertEqual(second_messages[-1]["tool_call_id"], "call-1")


if __name__ == "__main__":
    unittest.main()
