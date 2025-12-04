import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies that are hard to install or not needed for this test
sys.modules['kokoro'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['src.core.synthesizer'] = MagicMock()
sys.modules['src.utils.gpu'] = MagicMock()
sys.modules['src.utils.gpu'].get_gpu_info.return_value = (False, "Mock GPU")

from PySide6.QtWidgets import QApplication

# Ensure QApplication exists
if not QApplication.instance():
    app = QApplication(sys.argv)

from src.gui.main_window import MainWindow

class TestMainWindowFix(unittest.TestCase):
    @patch('src.gui.main_window.ExtractionWorker')
    @patch('src.gui.main_window.SynthesisWorker')
    def test_start_conversion_no_crash(self, mock_synthesis, mock_extraction):
        # Setup
        window = MainWindow()
        
        # Mock necessary components to bypass checks
        window.chapters = [MagicMock()]
        window.chapter_list = MagicMock()
        window.chapter_list.get_selected_chapters.return_value = [MagicMock()]
        window.controls = MagicMock()
        window.controls.get_settings.return_value = {
            'voice': 'af_sky',
            'speed': 1.0,
            'sentence_pause': 0.2,
            'comma_pause': 0.1
        }
        
        # Mock QFileDialog to return a path immediately
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=('dummy.m4b', 'Audiobook (*.m4b)')):
            # Execute - this should NOT raise AttributeError
            try:
                window.start_conversion()
            except AttributeError as e:
                self.fail(f"start_conversion raised AttributeError: {e}")
            except Exception as e:
                # Other errors might happen due to mocking, but we specifically care about AttributeError on btn_convert
                pass
        
        # Verify button text changed (proving it accessed the button correctly)
        self.assertEqual(window.btn_convert.text(), "Cancel Conversion")

if __name__ == '__main__':
    unittest.main()
