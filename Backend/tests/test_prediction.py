"""Real-model regression and HTTP tests. Run: python -m unittest discover -s tests -v."""
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from unittest.mock import patch

import numpy as np
from fastapi import HTTPException
from pydantic import ValidationError

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "src"))

from api.routes import get_options, predict_price
from api.schemas import CarInput
from models.predict import CarPricePredictor

BASELINE = json.loads((BACKEND / "tests/fixtures/inference_baseline.json").read_text(encoding="utf-8"))


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = CarPricePredictor()

    def test_original_features_and_predictions_are_identical(self):
        for fixture in BASELINE["fixtures"]:
            with self.subTest(car=fixture["input"]["Marque"]):
                car = CarInput.model_validate(fixture["input"])
                payload = car.model_dump(by_alias=True)
                actual = self.predictor.preprocess_input(payload)
                self.assertEqual(list(actual.columns), list(fixture["features"]))
                np.testing.assert_array_equal(actual.iloc[0].values, list(fixture["features"].values()))
                self.assertEqual(self.predictor.predict(payload), fixture["price"])

    def test_model_data_training_and_evaluation_files_are_unchanged(self):
        for name, digest in BASELINE["hashes"].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((BACKEND / name).read_bytes()).hexdigest(), digest)

    def test_invalid_input_is_rejected(self):
        invalid = {
            "Marque": " ", "Modèle": "", "Localisation": "",
            "Kilométrage": "-100", "Année-Modèle": 2099, "Puissance fiscale": "0 CV",
            "Nombre de portes": 0, "État": "Moyen", "Type de carburant": "invalid",
            "Boite de vitesses": "invalid", "Équipements": ["invalid"],
        }
        for key, value in invalid.items():
            with self.subTest(field=key), self.assertRaises(ValidationError):
                CarInput.model_validate({**BASELINE["fixtures"][0]["input"], key: value})

    def test_mileage_formats_and_upper_range(self):
        for mileage in ["0", 85000, "85 000", "50 000 - 74 999", "500 000+", "Plus de 500 000"]:
            with self.subTest(mileage=mileage):
                car = CarInput.model_validate({**BASELINE["fixtures"][0]["input"], "Kilométrage": mileage})
                self.assertGreater(self.predictor.predict(car.model_dump(by_alias=True)), 0)
        for mileage in ["90000-100", "abc", "nan", "1000001", True]:
            with self.subTest(mileage=mileage), self.assertRaises(ValidationError):
                CarInput.model_validate({**BASELINE["fixtures"][0]["input"], "Kilométrage": mileage})

    def test_options_are_derived_from_original_mapping(self):
        options = get_options(self.predictor)
        self.assertEqual(set(options["brands"]), set(self.predictor.mapping_df["Marque"].dropna()))
        self.assertIn("Clio", options["models"]["Renault"])
        self.assertIn("Electrique", options["fuels"])
        self.assertNotIn("Climatisation automatique", options["equipment"])

    def test_internal_errors_are_not_exposed(self):
        car = CarInput.model_validate(BASELINE["fixtures"][0]["input"])
        with patch.object(self.predictor, "predict", side_effect=RuntimeError("private filesystem detail")):
            with self.assertRaises(HTTPException) as error:
                predict_price(car, self.predictor)
        self.assertEqual(error.exception.status_code, 500)
        self.assertNotIn("private filesystem", error.exception.detail)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind an available loopback port so an existing user server is never stopped.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.url = f"http://127.0.0.1:{port}"
        cls.server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", "src", "--port", str(port)],
            cwd=BACKEND, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            for _ in range(120):
                if cls.server.poll() is not None:
                    raise RuntimeError("API test server failed to start")
                try:
                    with urlopen(cls.url + "/health", timeout=1):
                        return
                except (URLError, TimeoutError):
                    time.sleep(0.25)
            raise RuntimeError("API test server startup timed out")
        except Exception:
            cls.server.terminate()
            cls.server.wait(timeout=10)
            raise

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.server.wait(timeout=10)

    def request(self, path, body=None, headers=None, method=None):
        request = Request(self.url + path, data=json.dumps(body).encode() if body is not None else None,
                          headers={"Content-Type": "application/json", **(headers or {})}, method=method)
        try:
            response = urlopen(request, timeout=30)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read()
            return response.status, response.headers, json.loads(raw) if raw and raw != b"OK" else None

    def test_real_predictions_over_http(self):
        for fixture in BASELINE["fixtures"]:
            with self.subTest(car=fixture["input"]["Marque"]):
                status, _, data = self.request("/predict", fixture["input"])
                self.assertEqual(status, 200)
                self.assertEqual(data["predicted_price"], fixture["price"])
                self.assertEqual(data["estimated_tax"], fixture["price"] * 0.1)

    def test_invalid_request_returns_serializable_field_errors(self):
        status, _, data = self.request("/predict", {**BASELINE["fixtures"][0]["input"], "Kilométrage": "bad"})
        self.assertEqual(status, 422)
        self.assertEqual(data["detail"][0]["loc"], ["body", "Kilométrage"])

    def test_missing_fields(self):
        status, _, data = self.request("/predict", {})
        self.assertEqual(status, 422)
        self.assertGreater(len(data["detail"]), 5)

    def test_options_and_health(self):
        self.assertEqual(self.request("/health")[2], {"status": "healthy"})
        status, _, data = self.request("/options")
        self.assertEqual(status, 200)
        self.assertIn("Renault", data["brands"])

    def test_frontend_cors_preflight(self):
        for origin in ["http://localhost:5173", "http://127.0.0.1:5173"]:
            status, headers, _ = self.request("/predict", method="OPTIONS", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            })
            self.assertEqual(status, 200)
            self.assertEqual(headers["Access-Control-Allow-Origin"], origin)


if __name__ == "__main__":
    unittest.main()
