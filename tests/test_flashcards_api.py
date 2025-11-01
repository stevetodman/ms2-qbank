from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import create_engine

from flashcards import create_app
from flashcards.models import DeckType


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app = create_app(engine=engine, seed_path=tmp_path / "seed.json")
    with TestClient(app) as test_client:
        yield test_client


def _create_deck(client: TestClient, **overrides: object) -> dict[str, object]:
    payload = {
        "name": "Neuroanatomy Highlights",
        "description": "Rapid review of motor pathways and cranial nerves.",
        "deck_type": DeckType.READY.value,
    }
    payload.update(overrides)
    response = client.post("/decks", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_list_update_delete_deck(client: TestClient) -> None:
    created = _create_deck(client)

    response = client.get("/decks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == created["name"]
    assert data[0]["card_count"] == 0

    update_payload = {"description": "Updated description", "deck_type": DeckType.SMART.value}
    response = client.put(f"/decks/{created['id']}", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["description"] == "Updated description"
    assert updated["deck_type"] == DeckType.SMART.value

    response = client.get(f"/decks/{created['id']}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == created["id"]
    assert detail["card_count"] == 0
    assert detail["cards"] == []

    response = client.delete(f"/decks/{created['id']}")
    assert response.status_code == 204

    response = client.get("/decks")
    assert response.status_code == 200
    assert response.json() == []


def test_card_crud_flow(client: TestClient) -> None:
    deck = _create_deck(client)

    card_payload = {
        "prompt": "What neurotransmitter is depleted in Parkinson disease?",
        "answer": "Dopamine in the substantia nigra pars compacta.",
        "tags": ["neurology"],
    }
    response = client.post(f"/decks/{deck['id']}/cards", json=card_payload)
    assert response.status_code == 201
    card = response.json()
    assert card["deck_id"] == deck["id"]

    response = client.get(f"/decks/{deck['id']}/cards")
    assert response.status_code == 200
    cards = response.json()
    assert len(cards) == 1
    assert cards[0]["prompt"].startswith("What neurotransmitter")

    response = client.get(f"/decks/{deck['id']}/cards/{card['id']}")
    assert response.status_code == 200
    detail = response.json()
    assert detail["answer"].startswith("Dopamine")

    update_payload = {"explanation": "Loss of dopaminergic neurons reduces direct pathway signaling."}
    response = client.put(f"/decks/{deck['id']}/cards/{card['id']}", json=update_payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["explanation"].startswith("Loss of dopaminergic")

    response = client.delete(f"/decks/{deck['id']}/cards/{card['id']}")
    assert response.status_code == 204

    response = client.get(f"/decks/{deck['id']}/cards")
    assert response.status_code == 200
    assert response.json() == []


def test_seed_data_loaded(tmp_path: Path) -> None:
    seed_payload = [
        {
            "name": "Seed Deck",
            "description": "Preloaded content",
            "deck_type": "ready",
            "cards": [
                {"prompt": "A?", "answer": "B"},
            ],
        }
    ]
    seed_path = tmp_path / "seed.json"
    seed_path.write_text(json.dumps(seed_payload), encoding="utf-8")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    app = create_app(engine=engine, seed_path=seed_path)
    with TestClient(app) as test_client:
        response = test_client.get("/decks")
        assert response.status_code == 200
        decks = response.json()
        assert len(decks) == 1
        assert decks[0]["card_count"] == 1
        assert decks[0]["name"] == "Seed Deck"

