"""Tests for notes.py"""

import os
import tempfile
import unittest

import notes as note_store


class NotesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self._tmp.close()
        note_store.NOTES_FILE = self._tmp.name
        # start with empty file
        with open(self._tmp.name, "w") as f:
            f.write("[]")

    def tearDown(self):
        os.unlink(self._tmp.name)

    def test_add_and_list(self):
        note_store.add("hello world")
        notes = note_store.list_all()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["text"], "hello world")

    def test_add_with_tags(self):
        note_store.add("tagged note", ["work", "urgent"])
        notes = note_store.list_all()
        self.assertEqual(notes[0]["tags"], ["work", "urgent"])

    def test_search_finds_match(self):
        note_store.add("buy groceries")
        note_store.add("read a book")
        results = note_store.search("groceries")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "buy groceries")

    def test_search_case_insensitive(self):
        note_store.add("Meeting with Alice")
        results = note_store.search("meeting")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        note_store.add("hello")
        results = note_store.search("xyz")
        self.assertEqual(results, [])

    def test_delete(self):
        note_store.add("to delete")
        note_id = note_store.list_all()[0]["id"]
        ok = note_store.delete(note_id)
        self.assertTrue(ok)
        self.assertEqual(note_store.list_all(), [])

    def test_delete_nonexistent(self):
        ok = note_store.delete(999)
        self.assertFalse(ok)

    def test_filter_by_tag_finds_match(self):
        note_store.add("note one", ["work"])
        note_store.add("note two", ["personal"])
        results = note_store.filter_by_tag("work")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "note one")

    def test_filter_by_tag_case_insensitive(self):
        note_store.add("note", ["Work"])
        results = note_store.filter_by_tag("work")
        self.assertEqual(len(results), 1)

    def test_filter_by_tag_no_match(self):
        note_store.add("note", ["personal"])
        results = note_store.filter_by_tag("work")
        self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()
