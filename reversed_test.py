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

"""Unit tests for the `reversed` module and its `Reversed` class."""

import unittest, string
from reversed import Reversed
alpha = string.ascii_lowercase

class TestReversed(unittest.TestCase):
    """
    Tests for the `Reversed` class.
    """
    
    def setUp(self):
        self.r_alpha = Reversed(alpha)
    
    def test_revinst(self):
        """
        Verify that calling `Reversed(seq)` when `seq` is a built-in explicit sequence (eg string)
        produces a `Reversed` instance as desired.
        """
        self.assertIsInstance(self.r_alpha, Reversed)
        self.assertEqual(self.r_alpha._seq, alpha)
    
    def test_of_range(self):
        """
        Verify that calling `Reversed(seq)` when `seq` is a range
        produces another range with parameters modified appropriately.
        """
        cases = ((100,), (5, 10), (20, 40, 3), (0, -100, -1), (20, -21, -5))
        for args in cases:
            r = range(*args)
            with self.subTest(case=r):
                self.assertEqual(Reversed(r), r[::-1])
    
    def test_len(self):
        self.assertEqual(len(alpha), len(self.r_alpha))
    
    def test_contains(self):
        for c in string.printable:
            with self.subTest(c=c):
                self.assertEqual(c in alpha, c in self.r_alpha)
    
    def test_iter(self):
        with self.subTest("iter"):
            for a, b in zip(reversed(alpha), iter(self.r_alpha)):
                self.assertEqual(a, b)
        with self.subTest("reversed"):
            for a, b in zip(iter(alpha), reversed(self.r_alpha)):
                self.assertEqual(a, b)
    
    def test_double_reverse(self):
        self.assertIs(Reversed(self.r_alpha), alpha)
        
    def test_count(self):
        s = ''.join(alpha[i:i+5] for i in range(len(alpha)-4))
        r_s = Reversed(s)
        for c in alpha:
            with self.subTest(c=c):
                self.assertEqual(r_s.count(c), s.count(c))
    #similar strategy for index
    #& work on getitem

if __name__ == '__main__':
    unittest.main()