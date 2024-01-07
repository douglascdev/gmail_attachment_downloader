import unittest
from pathlib import Path

from gmail_attachment_downloader.__main__ import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    def test_directory_traversal(self):
        current_folder = Path.cwd()
        # Try to access a file outside of the current folder
        traversal_attempt = current_folder / ".." / "file.txt"
        sanitized_path = Path(sanitize_filename(str(traversal_attempt)))

        try:
            sanitized_path.resolve().relative_to(current_folder)
        except ValueError:
            self.fail(
                "Sanitized path outside of current folder, directory traversal successful"
            )

    def test_extension_is_kept(self):
        sanitized_path = Path(sanitize_filename("test.txt"))
        self.assertEqual(sanitized_path.suffix, ".txt")

    def test_special_characters_are_replaced(self):
        special_chars = " *?|!@#$%^&*()_+{}[];':,<>///?`~\\\n\r\""
        sanitized_path = sanitize_filename(f"test{special_chars}.txt")
        self.assertEqual(sanitized_path, f"test{'_'*len(special_chars)}.txt")


if __name__ == "__main__":
    unittest.main()
