"""Unit tests for NIYAM's allowlisted local desktop actions."""

import re
import unittest
from unittest.mock import patch

import tools
from tools import handle_local_action


class LocalActionTests(unittest.TestCase):
    @patch("tools.subprocess.Popen")
    def test_open_notepad_uses_fixed_executable_without_shell(self, popen):
        result = handle_local_action("open notepad")
        popen.assert_called_once_with(["notepad.exe"], shell=False, close_fds=True)
        self.assertIn("Notepad is opening", result)

    @patch("tools.subprocess.Popen")
    def test_polite_case_insensitive_notepad_request(self, popen):
        result = handle_local_action("NIYAM, please open the Notepad")
        popen.assert_called_once_with(["notepad.exe"], shell=False, close_fds=True)
        self.assertIn("Notepad is opening", result)

    @patch("tools.subprocess.Popen")
    def test_open_calculator_uses_fixed_executable_without_shell(self, popen):
        result = handle_local_action("launch calculator")
        popen.assert_called_once_with(["calc.exe"], shell=False, close_fds=True)
        self.assertIn("Calculator is opening", result)

    @patch("tools.subprocess.Popen", side_effect=OSError("not available"))
    def test_application_launch_error_is_reported(self, popen):
        result = handle_local_action("open notepad")
        self.assertIn("couldn't open Notepad", result)

    @patch("tools.webbrowser.open_new_tab", return_value=True)
    def test_youtube_opens_only_approved_url(self, open_tab):
        result = handle_local_action("please open YouTube")
        open_tab.assert_called_once_with("https://www.youtube.com/")
        self.assertIn("YouTube is opening", result)

    @patch("tools.webbrowser.open_new_tab", return_value=False)
    def test_browser_failure_is_reported(self, open_tab):
        result = handle_local_action("open youtube")
        self.assertIn("couldn't open the browser", result)

    @patch("tools.subprocess.Popen")
    @patch("tools.webbrowser.open_new_tab")
    def test_arbitrary_command_is_not_executed(self, open_tab, popen):
        result = handle_local_action("run powershell Remove-Item C:\\important.txt")
        self.assertIsNone(result)
        popen.assert_not_called()
        open_tab.assert_not_called()

    @patch("tools.webbrowser.open_new_tab")
    def test_arbitrary_url_is_not_opened(self, open_tab):
        result = handle_local_action("open https://example.com")
        self.assertIsNone(result)
        open_tab.assert_not_called()

    def test_unknown_action_is_not_handled(self):
        self.assertIsNone(handle_local_action("delete my files"))

    def test_time_response_has_readable_clock(self):
        result = handle_local_action("what time is it")
        self.assertRegex(result, re.compile(r"^It's \d{2}:\d{2} [AP]M \(.+\)\.$"))


if __name__ == "__main__":
    unittest.main()
