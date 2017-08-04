import unittest
from gradSearchCapsTable import *

class TestCalculateStationObj(unittest.TestCase):
    # Testing calculateStationObj(arrowDict, sid, level, capacity)
    def test_oneStationOneRep_overCap(self):
        arrowDict = {0: {1: [1, 1, 1, 1]}}
        self.assertEqual(calculateStationObj(arrowDict, 1, 0, 3), 1)

    def test_oneStationOneRep_underZero(self):
        arrowDict = {0: {1: [-1, -1, -1, -1]}}
        self.assertEqual(calculateStationObj(arrowDict, 1, 0, 3), 4)

    def test_twoStationOneRep(self):
        arrowDict = {0: {1: [1, 1, 1, 1], 2: [1, 1, 1, 1]}}
        self.assertEqual(calculateStationObj(arrowDict, 1, 0, 3), 1)

    def test_oneStationTwoRep(self):
        arrowDict = {0: {1: [1, 1, 1, 1]}, 1: {1:[1, 1, 1, 1]}}
        self.assertEqual(calculateStationObj(arrowDict, 1, 0, 3), 1)

class TestCalculateTotalObj(unittest.TestCase):
    # Testing calculateTotalObj(arrowDict, level, capacity)
    def test_twoStationOneRep(self):
        arrowDict = {0: {1: [1, 1, 1, 1], 2: [1, 1, 1, 1]}}
        self.assertEqual(calculateTotalObj(arrowDict, {1: 0, 2: 0}, {1: 1, 2: 2}), 5)

    def test_twoStationTwoRep(self):
        arrowDict = {0: {1: [1, 1, 1, 1], 2: [1, 1, 1, 1]}, 1: {1: [1, 1, 1, 1], 2: [1, 1, 1, 1]}}
        self.assertEqual(calculateTotalObj(arrowDict, {1: 0, 2: 0}, {1: 1, 2: 2}), 5)
