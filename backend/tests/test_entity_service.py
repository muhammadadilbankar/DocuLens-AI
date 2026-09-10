import unittest
from types import SimpleNamespace

from app.services.entity_service import extract_entities


class FakeNlp:
    def __call__(self, text):
        person = "Mohammed Adil"
        organization = "ARCIL"
        return SimpleNamespace(
            ents=[
                SimpleNamespace(
                    text=person,
                    label_="PERSON",
                    start_char=text.index(person),
                    end_char=text.index(person) + len(person),
                ),
                SimpleNamespace(
                    text=organization,
                    label_="ORG",
                    start_char=text.index(organization),
                    end_char=text.index(organization) + len(organization),
                ),
                SimpleNamespace(
                    text="PAN",
                    label_="ORG",
                    start_char=text.index("PAN:"),
                    end_char=text.index("PAN:") + 3,
                ),
            ]
        )


class EntityServiceTests(unittest.TestCase):
    def test_combines_regex_and_spacy_entities_with_traceability(self) -> None:
        lines = [
            "Borrower: Mohammed Adil",
            "Lender: ARCIL",
            "Loan Amount: INR 250,000",
            "Account Number: ARCIL-2026-105",
            "Due Date: 10/09/2026",
            "PAN: ABCDE1234F",
        ]
        blocks = [
            SimpleNamespace(
                text=line,
                bounding_box=[[0, index * 20], [500, index * 20], [500, index * 20 + 15], [0, index * 20 + 15]],
            )
            for index, line in enumerate(lines)
        ]

        results = extract_entities("\n".join(lines), blocks, FakeNlp())
        values = {(entity.entity_type, entity.entity_value) for entity in results}

        self.assertIn(("PERSON", "Mohammed Adil"), values)
        self.assertIn(("ORGANIZATION", "ARCIL"), values)
        self.assertIn(("MONEY", "INR 250,000"), values)
        self.assertIn(("ACCOUNT_NUMBER", "ARCIL-2026-105"), values)
        self.assertIn(("DATE", "10/09/2026"), values)
        self.assertIn(("PAN", "ABCDE1234F"), values)
        self.assertNotIn(("ORGANIZATION", "PAN"), values)
        self.assertEqual(
            sum(
                entity.entity_type == "PERSON"
                and entity.entity_value == "Mohammed Adil"
                for entity in results
            ),
            1,
        )

        money = next(entity for entity in results if entity.entity_type == "MONEY")
        self.assertEqual(money.source, "REGEX")
        self.assertEqual(money.confidence, 1.0)
        self.assertEqual(
            money.bounding_box,
            [[0.0, 40.0], [500.0, 40.0], [500.0, 55.0], [0.0, 55.0]],
        )

    def test_empty_page_returns_no_entities(self) -> None:
        self.assertEqual(extract_entities("", [], FakeNlp()), [])


if __name__ == "__main__":
    unittest.main()
