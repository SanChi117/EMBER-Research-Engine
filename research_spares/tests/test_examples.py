import unittest
from ember_spares.examples import run_all
from ember_spares.registry import REGISTRY

class FullPlugAndPlayFixtures(unittest.TestCase):
    def test_all_37_execute_with_valid_json(self):
        results=run_all()
        self.assertEqual(set(results), {c.id for c in REGISTRY})
        self.assertEqual(len(results),37)
        self.assertEqual(results['Z09'],'AMBIGUOUS')
        self.assertAlmostEqual(results['Z22'],14/30)
        self.assertEqual(results['Z07'],[True,'OK'])
        self.assertEqual(results['Z06']['quantity'],1)

if __name__=='__main__': unittest.main()
