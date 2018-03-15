#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##################################################################################
# seqtools Copyright (C) 2018 Simon Wyatt <simon.d.wyatt@gmail.com>              #
# This program is free software: you can redistribute it and/or modify it under  #
# the terms of the GNU General Public License as published by the Free Software  #
# Foundation, either version 3 of the License, or (at your option) any later     #
# version.                                                                       #
#                                                                                #
# This program is distributed in the hope that it will be useful, but WITHOUT    #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS  #
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. #
#                                                                                #
# You should have received a copy of the GNU General Public License along with   #
# this program. If not, see <http://www.gnu.org/licenses/>.                      #
##################################################################################

"""Unit tests for the `combinatorics` module using the built-in `unittest` module."""

import unittest
import combinatorics

class TestProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        empty   = combinatorics.Product()
        singles = combinatorics.Product((1,), (2,), (3,), (4,))
        A0      = combinatorics.Product("ABC", (0,1))
        B3      = combinatorics.Product(range(2), repeat=3)
        ABC3    = combinatorics.Product("ABC", repeat=3)
        huge    = combinatorics.Product(range(10**6), repeat=10)
        cls._testSubjects = (empty, singles, A0, B3, ABC3, huge)
    
    def test_len(self):
        expected_lengths = (1, 1, 6, 8, 27)#, 10**60) #Too big for CPython, separated to test_len_huge
        for P, L in zip(self._testSubjects, expected_lengths):
            with self.subTest(P=P, expected_length=L):
                self.assertEqual(len(P), L)
    
    def test_len_huge(self):
        huge = self._testSubjects[-1]
        self.assertEqual(huge.len(), 10**60)
    
    def test_get_one_item(self):
        indices  = (0, 0, 2, -3, 26, 785979398597554673765267388740066098873495547967682668161773)
        expected = (
            (),
            (1, 2, 3, 4),
            ('B', 0),
            (1, 0, 1),
            ('C', 'C', 'C'),
            (785979, 398597, 554673, 765267, 388740,  66098, 873495, 547967, 682668, 161773),
        )
        for P, index, item in zip(self._testSubjects, indices, expected):
            with self.subTest(P=P, index=index, expected_item=item):
                self.assertEqual(P[index], item)
    
    def test_get_bad_item(self):
        indices  = (1, -2, 6)
        for P, index in zip(self._testSubjects, indices):
            with self.subTest(P=P, index=index):
                with self.assertRaises(IndexError):
                    P[index]
        

if __name__ == '__main__':
    unittest.main()