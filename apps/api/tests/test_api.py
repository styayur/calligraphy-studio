from __future__ import annotations

from fastapi.testclient import TestClient


def test_search_and_filters(client: TestClient) -> None:
    response = client.get("/api/search", params={"q": "山", "dataset": "Demo"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert {item["source"]["style"] for item in payload["items"]} == {"楷书", "行书"}
    assert payload["items"][0]["provenance"]["type"] == "fallback"
    assert payload["items"][0]["source"]["license"] == "CC0-1.0"

    filtered = client.get(
        "/api/search",
        params={"q": "山", "style": "行书", "dataset": "Demo"},
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


def test_cursive_search(client: TestClient) -> None:
    response = client.get(
        "/api/search",
        params={
            "q": "春",
            "style": "草书",
            "dataset": "NCCU Cursive Chinese Calligraphy Dataset",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert all(
        item["source"]["dataset"] == "NCCU Cursive Chinese Calligraphy Dataset"
        for item in payload["items"]
    )
    assert all(item["source"]["license"] == "MIT" for item in payload["items"])


def test_metadata_and_single_glyph(client: TestClient) -> None:
    glyph = client.get("/api/search", params={"q": "水", "dataset": "Demo"}).json()["items"][0]
    response = client.get(f"/api/glyph/{glyph['id']}")
    assert response.status_code == 200
    assert response.json()["character"] == "水"

    metadata = client.get("/api/meta").json()
    assert {"演示·王体", "演示·颜体"}.issubset(
        {item["name"] for item in metadata["calligraphers"]}
    )
    assert {item["name"] for item in metadata["styles"]} == {"楷书", "行书", "草书"}
    assert set(metadata["datasets"]) == {
        "Demo",
        "NCCU Cursive Chinese Calligraphy Dataset",
        "OFL Calligraphy Fonts",
    }


def test_ofl_font_search(client: TestClient) -> None:
    regular = client.get(
        "/api/search",
        params={"q": "山", "style": "楷书", "dataset": "OFL Calligraphy Fonts"},
    )
    running = client.get(
        "/api/search",
        params={"q": "山", "style": "行书", "dataset": "OFL Calligraphy Fonts"},
    )
    cursive = client.get(
        "/api/search",
        params={"q": "山", "style": "草书", "dataset": "OFL Calligraphy Fonts"},
    )
    assert regular.json()["total"] == 1
    assert running.json()["total"] == 1
    assert cursive.json()["total"] == 1
    item = regular.json()["items"][0]
    assert item["provenance"]["type"] == "font"
    assert item["source"]["license"] == "OFL-1.1"


def test_project_round_trip(client: TestClient) -> None:
    glyph = client.get("/api/search", params={"q": "云", "dataset": "Demo"}).json()["items"][0]
    instance = {**glyph, "id": "instance-1", "glyph_id": glyph["id"]}
    instance["transform"]["x"] = 320
    instance["transform"]["y"] = 180
    instance["appearance"]["blendMode"] = "multiply"
    document = {
        "version": 1,
        "canvas": {"width": 1200, "height": 800, "background": "#f8f4ea"},
        "glyphs": [instance],
    }

    created = client.post("/api/projects", json={"name": "测试项目", "document": document})
    assert created.status_code == 201
    project_id = created.json()["id"]

    loaded = client.get(f"/api/projects/{project_id}")
    assert loaded.status_code == 200
    assert loaded.json()["document"]["glyphs"][0]["appearance"]["blendMode"] == "multiply"

    document["glyphs"][0]["transform"]["rotation"] = 12
    updated = client.put(
        f"/api/projects/{project_id}",
        json={"name": "更新后的项目", "document": document},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "更新后的项目"
    assert updated.json()["document"]["glyphs"][0]["transform"]["rotation"] == 12


def test_fallback_real_and_missing(client: TestClient) -> None:
    real = client.post(
        "/api/fallback/resolve",
        json={"character": "山", "calligrapher": "演示·王体", "style": "行书"},
    )
    assert real.status_code == 200
    assert real.json()["level"] == 1
    assert real.json()["resolved"] is True

    missing = client.post(
        "/api/fallback/resolve",
        json={"character": "龍", "use_structural_fallback": False},
    )
    assert missing.status_code == 200
    assert missing.json()["level"] == 3
    assert missing.json()["resolved"] is False


def test_cursive_batch_composition(client: TestClient) -> None:
    response = client.post(
        "/api/compose/batch",
        json={
            "text": "春山",
            "layout": "grid",
            "columns": 2,
            "cell_width": 180,
            "cell_height": 180,
            "gap_x": 4,
            "gap_y": 4,
            "start_x": 80,
            "start_y": 80,
            "style": "草书",
            "dataset": "NCCU Cursive Chinese Calligraphy Dataset",
            "use_structural_fallback": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total_characters"] == 2
    assert payload["resolved_characters"] == 2
    assert payload["missing"] == []
    assert all(item["glyph"]["source"]["style"] == "草书" for item in payload["placements"])


def test_visual_similarity_index(client: TestClient) -> None:
    target = client.get(
        "/api/search",
        params={"q": "山", "style": "草书", "limit": 1},
    ).json()["items"][0]
    indexed = client.post("/api/similarity/reindex", params={"limit": 200})
    assert indexed.status_code == 200
    index_payload = indexed.json()
    assert index_payload["indexed"] > 0, index_payload

    response = client.get(
        f"/api/similarity/{target['id']}",
        params={"limit": 5, "same_style": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "visual-geometry-256-v1"
    assert payload["items"]
    assert payload["items"][0]["score"] > 0
