"""
Unit tests for CLI commands execution.
"""

import unittest
from unittest.mock import patch
import sys
from preuni_system.cli import main


class TestCLI(unittest.TestCase):

    def test_cli_stats(self):
        with patch.object(sys, 'argv', ['preuni', 'stats']):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_cli_digest_preview(self):
        with patch.object(sys, 'argv', ['preuni', 'digest', '--preview']):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

    def test_cli_alert_preview(self):
        with patch.object(sys, 'argv', ['preuni', 'alert', '--preview']):
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)


if __name__ == "__main__":
    unittest.main()
