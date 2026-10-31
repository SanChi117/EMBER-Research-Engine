import unittest
import ember_spares

class PackageTests(unittest.TestCase):
    def test_package_has_no_auto_execution(self):
        self.assertEqual(ember_spares.__version__,'0.3.0')
        self.assertFalse(hasattr(ember_spares,'place_order'))
        self.assertFalse(hasattr(ember_spares,'run_backtest'))

if __name__=='__main__': unittest.main()
