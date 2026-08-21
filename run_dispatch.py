"""Run the logistics tool loop with local, auditable tool handlers."""

import os

from logistics_agent import LogisticsAgent


SHIPMENTS = {
    "SHP-1042": {"status": "ready", "destination_zone": "east-2"},
}


def lookup_shipment(shipment_id: str) -> dict[str, str]:
    return {"shipment_id": shipment_id, **SHIPMENTS[shipment_id]}


def schedule_pickup(shipment_id: str, window: str) -> dict[str, str]:
    return {
        "shipment_id": shipment_id,
        "window": window,
        "pickup_status": "scheduled",
    }


def main() -> None:
    agent = LogisticsAgent(
        api_key=os.environ["INFRAI_API_KEY"],
        handlers={
            "lookup_shipment": lookup_shipment,
            "schedule_pickup": schedule_pickup,
        },
    )
    result = agent.run(
        "Check shipment SHP-1042 and schedule pickup for 14:00-16:00 if it is ready."
    )
    print(result)


if __name__ == "__main__":
    main()
