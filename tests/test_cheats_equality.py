from classes.cheat import *
from classes.poke import *
import unittest

class TestCheatsEquality(unittest.TestCase):

    def test_quantity(self):
        c = Cheat('Cheat 1')
        c.addPoke(22222, 255)
        c.addPoke(22223, 255)
        c1 = Cheat('Cheat 2')
        c1.addPoke(22222, 255)
        self.assertFalse(c==c1)

    def test_equal(self):
        c = Cheat('Cheat 1')
        c.addPoke(22222, 255)
        c.addPoke(22223, 255)
        c1 = Cheat('Cheat 2')
        c1.addPoke(22222, 255)
        c1.addPoke(22223, 255)
        self.assertTrue(c==c1)

    def test_unequal(self):
        c = Cheat('Cheat 1')
        c.addPoke(22222, 255)
        c.addPoke(22223, 255)
        c1 = Cheat('Cheat 2')
        c1.addPoke(22222, 255)
        c1.addPoke(22223, 254)
        self.assertNotEqual(c, c1)
        c1 = Cheat('Cheat 2')
        c1.addPoke(22222, 255)
        c1.addPoke(22224, 255)
        self.assertNotEqual(c, c1)

    def test_adding_same_poke(self):
        c = Cheat('Cheat 1')
        c.addPoke(22222, 255)
        c.addPoke(22222, 255)
        self.assertEqual(len(c.pokes), 1)

    def test_adding_illegal_poke(self):
        c = Cheat('Cheat 1')
        with self.assertRaises(ValueError):
            c.addPoke(0, 0)
        with self.assertRaises(ValueError):
            c.addPoke(22222, 257)




