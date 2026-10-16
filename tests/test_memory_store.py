r"""Automated tests for NIYAM's local, opt-in memory store.

All tests use temporary directories; they never read or modify data/memories.json.
Run from the NIYAM project root with:
    .\.venv\Scripts\python.exe -m unittest discover -s .\tests -p "test_*.py" -v
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import memory_store
from memory_store import MemoryStorageError, MemoryStore, handle_memory_command


class MemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_file = Path(self.temp_dir.name) / "data" / "memories.json"
        self.store = MemoryStore(self.memory_file)
        memory_store._CLEAR_PENDING = False

    def tearDown(self):
        memory_store._CLEAR_PENDING = False
        self.temp_dir.cleanup()

    def test_missing_file_is_treated_as_empty_without_creating_it(self):
        self.assertEqual(self.store.list_memories(), [])
        self.assertFalse(self.memory_file.exists())

    def test_memory_persists_after_store_is_recreated(self):
        item, added = self.store.add_memory("I prefer concise answers")
        self.assertTrue(added)
        self.assertEqual(item["id"], 1)

        restarted_store = MemoryStore(self.memory_file)
        self.assertEqual(restarted_store.list_memories()[0]["text"], "I prefer concise answers")

    def test_whitespace_is_normalized(self):
        item, added = self.store.add_memory("  I   use\tPowerShell  ")
        self.assertTrue(added)
        self.assertEqual(item["text"], "I use PowerShell")

    def test_case_insensitive_duplicate_is_not_added(self):
        first, first_added = self.store.add_memory("I use PowerShell")
        second, second_added = self.store.add_memory("i USE powershell")
        self.assertTrue(first_added)
        self.assertFalse(second_added)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_ids_are_not_reused_after_deleting_one_memory(self):
        first, _ = self.store.add_memory("first fact")
        second, _ = self.store.add_memory("second fact")
        third, _ = self.store.add_memory("third fact")
        self.assertEqual((first["id"], second["id"], third["id"]), (1, 2, 3))
        self.store.forget_id(2)
        next_item, _ = self.store.add_memory("fourth fact")
        self.assertEqual(next_item["id"], 4)

    def test_next_id_is_preserved_after_clear_all(self):
        self.store.add_memory("one")
        self.store.add_memory("two")
        self.assertEqual(self.store.clear_all(), 2)
        self.assertEqual(self.store.list_memories(), [])
        item, _ = self.store.add_memory("new fact")
        self.assertEqual(item["id"], 3)

    def test_empty_memory_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add_memory("   \t  ")
        self.assertEqual(self.store.list_memories(), [])

    def test_memory_longer_than_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add_memory("x" * (memory_store.MAX_MEMORY_LENGTH + 1))
        self.assertEqual(self.store.list_memories(), [])

    def test_memory_at_limit_is_accepted(self):
        text = "x" * memory_store.MAX_MEMORY_LENGTH
        item, added = self.store.add_memory(text)
        self.assertTrue(added)
        self.assertEqual(len(item["text"]), memory_store.MAX_MEMORY_LENGTH)

    def test_null_control_character_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add_memory("hello\x00world")
        self.assertEqual(self.store.list_memories(), [])

    def test_memory_capacity_is_enforced(self):
        with patch.object(memory_store, "MAX_MEMORIES", 2):
            self.store.add_memory("one")
            self.store.add_memory("two")
            with self.assertRaises(ValueError):
                self.store.add_memory("three")
        self.assertEqual(len(self.store.list_memories()), 2)

    def test_delete_by_id_only_removes_requested_memory(self):
        self.store.add_memory("first fact")
        self.store.add_memory("second fact")
        removed = self.store.forget_id(1)
        self.assertEqual(removed["text"], "first fact")
        self.assertEqual([m["text"] for m in self.store.list_memories()], ["second fact"])

    def test_delete_unknown_id_returns_none(self):
        self.assertIsNone(self.store.forget_id(999))

    def test_delete_exact_text_normalizes_whitespace_and_case(self):
        self.store.add_memory("I prefer dark mode")
        removed = self.store.forget_exact_text("  i   PREFER dark mode  ")
        self.assertIsNotNone(removed)
        self.assertEqual(self.store.list_memories(), [])

    def test_plain_statement_is_not_saved_automatically(self):
        result = handle_memory_command("My favorite color is blue", self.store)
        self.assertIsNone(result)
        self.assertEqual(self.store.list_memories(), [])

    def test_natural_save_list_and_delete_by_id(self):
        saved = handle_memory_command("remember that I use PowerShell", self.store)
        self.assertIn("Saved to memory [1]", saved)
        listing = handle_memory_command("what do you remember about me?", self.store)
        self.assertIn("I use PowerShell", listing)
        deleted = handle_memory_command("forget memory 1", self.store)
        self.assertIn("Deleted memory [1]", deleted)
        self.assertEqual(self.store.list_memories(), [])

    def test_duplicate_natural_save_reports_existing_id(self):
        handle_memory_command("remember that I use PowerShell", self.store)
        result = handle_memory_command("remember that i use powershell", self.store)
        self.assertIn("already saved as memory [1]", result)
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_clear_all_requires_confirmation(self):
        self.store.add_memory("I prefer dark mode")
        pending = handle_memory_command("forget all memories", self.store)
        self.assertIn("confirm clear memory", pending)
        self.assertEqual(len(self.store.list_memories()), 1)
        done = handle_memory_command("confirm clear memory", self.store)
        self.assertIn("deleted all 1 saved memory", done)
        self.assertEqual(self.store.list_memories(), [])

    def test_cancel_clear_does_not_delete_anything(self):
        self.store.add_memory("I prefer dark mode")
        handle_memory_command("forget all memories", self.store)
        response = handle_memory_command("cancel memory clear", self.store)
        self.assertIn("cancelled", response.lower())
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_unrelated_next_input_cancels_pending_clear(self):
        self.store.add_memory("I prefer dark mode")
        handle_memory_command("forget all memories", self.store)
        result = handle_memory_command("hello NIYAM", self.store)
        self.assertIsNone(result)
        confirmation = handle_memory_command("confirm clear memory", self.store)
        self.assertIn("No memory deletion is waiting", confirmation)
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_help_like_input_cancels_pending_clear_when_handler_is_called(self):
        """The application dispatcher must call the memory handler for every input."""
        self.store.add_memory("I prefer dark mode")
        handle_memory_command("forget all memories", self.store)
        self.assertIsNone(handle_memory_command("/help", self.store))
        confirmation = handle_memory_command("confirm clear memory", self.store)
        self.assertIn("No memory deletion is waiting", confirmation)
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_confirmation_without_pending_request_does_not_delete(self):
        self.store.add_memory("keep this fact")
        result = handle_memory_command("confirm clear memory", self.store)
        self.assertIn("No memory deletion is waiting", result)
        self.assertEqual(len(self.store.list_memories()), 1)

    def test_corrupt_file_is_not_overwritten(self):
        self.memory_file.parent.mkdir(parents=True)
        original = "not valid json"
        self.memory_file.write_text(original, encoding="utf-8")
        with self.assertRaises(MemoryStorageError):
            self.store.add_memory("I use PowerShell")
        self.assertEqual(self.memory_file.read_text(encoding="utf-8"), original)

    def test_unsupported_version_is_not_overwritten(self):
        self.memory_file.parent.mkdir(parents=True)
        original = json.dumps({"version": 99, "next_id": 1, "memories": []})
        self.memory_file.write_text(original, encoding="utf-8")
        with self.assertRaises(MemoryStorageError):
            self.store.list_memories()
        self.assertEqual(self.memory_file.read_text(encoding="utf-8"), original)

    def test_invalid_memory_structure_is_not_overwritten(self):
        self.memory_file.parent.mkdir(parents=True)
        original = json.dumps({"version": 1, "next_id": 1, "memories": "not-a-list"})
        self.memory_file.write_text(original, encoding="utf-8")
        with self.assertRaises(MemoryStorageError):
            self.store.list_memories()
        self.assertEqual(self.memory_file.read_text(encoding="utf-8"), original)

    def test_duplicate_memory_ids_are_rejected(self):
        self.memory_file.parent.mkdir(parents=True)
        original = json.dumps({
            "version": 1,
            "next_id": 3,
            "memories": [
                {"id": 1, "text": "one", "created_at": "now"},
                {"id": 1, "text": "duplicate", "created_at": "now"},
            ],
        })
        self.memory_file.write_text(original, encoding="utf-8")
        with self.assertRaises(MemoryStorageError):
            self.store.list_memories()
        self.assertEqual(self.memory_file.read_text(encoding="utf-8"), original)

    def test_stale_next_id_is_advanced_past_existing_ids(self):
        self.memory_file.parent.mkdir(parents=True)
        self.memory_file.write_text(json.dumps({
            "version": 1,
            "next_id": 1,
            "memories": [{"id": 5, "text": "existing", "created_at": "now"}],
        }), encoding="utf-8")
        item, _ = self.store.add_memory("next fact")
        self.assertEqual(item["id"], 6)

    def test_context_text_only_includes_configured_recent_memories(self):
        with patch.object(memory_store, "MAX_CONTEXT_MEMORIES", 2):
            self.store.add_memory("fact one")
            self.store.add_memory("fact two")
            self.store.add_memory("fact three")
            context = self.store.context_text()
        self.assertNotIn("[1] fact one", context)
        self.assertIn("[2] fact two", context)
        self.assertIn("[3] fact three", context)
        self.assertIn("1 older notes remain saved", context)


if __name__ == "__main__":
    unittest.main()
