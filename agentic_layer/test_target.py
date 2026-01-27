
import unittest
from target_script import add, subtract, multiply, divide

class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_multiply(self):
        self.assertEqual(multiply(3, 4), 12)
        
    def test_new_feature_power(self):
        # This will fail because power is not implemented yet
        from target_script import power
        self.assertEqual(power(2, 3), 8)

if __name__ == '__main__':
    unittest.main()
