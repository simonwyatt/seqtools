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

"""Unit tests for the `combinatorics` module.."""

import unittest, itertools
#import combinatorics
from combinatorics import Product
from reversed import Reversed

class TestProduct(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        empty   = Product()
        singles = Product((1,), (2,), (3,), (4,))
        A0      = Product("ABC", (0,1))
        B3      = Product(range(2), repeat=3)
        ABC3    = Product("ABC", repeat=3)
        huge    = Product(range(10**6), repeat=10)
        cls._testSubjects = (empty, singles, A0, B3, ABC3, huge)
    
    ################
    # Construction #
    ################
    
    def test_Reversed(self):
        empty, single, A0, B3, ABC3 = self._testSubjects[:5]
        params = (
            ( (), {} ),
            ( ((1,), (2,), (3,), (4,)), {} ),
            ( ("ABC", range(3), (False, True)), {}            ),
            ( ((0, 1),),                        {'repeat': 3} )
        )
        
        for args, kwargs in params:
            with self.subTest(args=args, kwargs=kwargs):
                instance  = Reversed(Product(*args, **kwargs))
                reference = tuple(itertools.product(*args, **kwargs))[::-1]
                
                # Length matches.
                self.assertEqual(len(instance), len(reference))
                
                # Items match, if any
                for i in range(-len(reference), len(reference)):
                    with self.subTest(pos = i):
                        self.assertEqual(instance[i], reference[i])
                
                # Boundaries match.
                for bad_i in (-len(reference) - 1, len(reference)):
                    with self.subTest(pos = bad_i):
                        with self.assertRaises(IndexError):
                            instance[bad_i]
                
                # Iteration produces same items.
                for (i, (got, expected)) in enumerate(zip(instance, reference)):
                    with self.subTest(pos = i):
                        self.assertEqual(got, expected)
                # We don't need the `itertools.zip_longest( ... , fillvalue=object())` idiom here
                # because we've already asserted that the lengths are equal.
                
    
    def test_empty_product(self):
        startstops = (None, 0, -1, 5, -5)
        steps = (None, 2, -1)
        
        product = Product()
        reference = ((),)
        
        for sliceargs in itertools.product(startstops, startstops, steps):
            index = slice(*sliceargs)
            sliceobj =   product[index]
            expected = reference[index]
            with self.subTest(index=index):
                # Length matches.
                self.assertEqual(len(sliceobj), len(expected))
                
                # If there's an item, check that it's retrieved as expected
                if len(expected) > 0:
                    for i in (0, -1):
                        self.assertEqual(sliceobj[i], expected[i])
                
                # Boundaries at expected locations.
                for bad_i in (-len(expected) - 1, len(expected)):
                    with self.subTest(pos = bad_i):
                        with self.assertRaises(IndexError):
                            sliceobj[bad_i]
    
    ##########
    # Length #
    ##########
    
    def test_len(self):
        expected_lengths = (1, 1, 6, 8, 27)#, 10**60) #Too big for CPython, separated to test_len_huge
        for P, L in zip(self._testSubjects, expected_lengths):
            with self.subTest(P=P, expected_length=L):
                self.assertEqual(len(P), L)
    
    def test_len_huge(self):
        huge = self._testSubjects[-1]
        self.assertEqual(huge.len(), 10**60)
    
    ###############
    # Item access #
    ###############
    
    def test_get_one_item(self):
        """Test that Product instances produce the correct items when subscripted."""
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
        """Test that Product instances raise the appropriate exception given an out-of-bounds index."""
        indices  = (1, -2, 6)
        for P, index in zip(self._testSubjects, indices):
            with self.subTest(P=P, index=index):
                with self.assertRaises(IndexError):
                    P[index]
                    
    def test_slicing(self):
        """
        Test that Product instances produce slice objects that behave correctly.
        """
        factor_sets = (
            ("ABC", "ABC", "ABC"),
            (range(3), range(4), range(3)),
            ("ABCD", (False, True), range(11))
        )
        startstops = (None, 0, -1, 3, -3, 6, -6, 20, -20, 99, -99)
        steps = (None, 1, -1, 3, -3, 99, -99)
        
        for factors in factor_sets:
            product   = Product(*factors)
            reference = tuple(itertools.product(*factors))        
            for sliceargs in itertools.product(startstops, startstops, steps):
                index = slice(*sliceargs)
            
                sliceobj =   product[index]
                expected = reference[index]
            
                with self.subTest(factors=factors, index=index):
                    # Length matches.
                    self.assertEqual(len(sliceobj), len(expected))
                
                    # Items equal at in-bounds indices.
                    for i in range(-len(expected), len(expected)):
                        with self.subTest(pos=i):
                            self.assertEqual(sliceobj[i], expected[i])
                
                    # Boundaries at expected locations.
                    for bad_i in (-len(expected) - 1, len(expected)):
                        with self.subTest(pos = bad_i):
                            with self.assertRaises(IndexError):
                                sliceobj[bad_i]
                
                    # Iteration produces expected items.
                    for (i, (x, y)) in enumerate(zip(sliceobj, expected)):
                        with self.subTest(pos=i):
                            self.assertEqual(x, y)
    
    #############
    # Iteration #
    #############
    
    def test_iter(self):
        params = (
            ( (), {} ),
            ( ((1,), (2,), (3,), (4,)), {} ),
            ( ("ABC", range(3), (False, True)), {}            ),
            ( ((0, 1),),                        {'repeat': 3} )
        )
        sentinel = object()
        
        for args, kwargs in params:
            with self.subTest(args=args, kwargs=kwargs):
                instance  = Product(*args, **kwargs)
                reference = tuple(itertools.product(*args, **kwargs))
                
                with self.subTest('forward'):                
                    for got, expected in itertools.zip_longest(instance, reference, fillvalue=sentinel):
                        self.assertEqual(got, expected)
                with self.subTest('reverse'):
                    for got, expected in itertools.zip_longest(reversed(instance), reversed(reference), fillvalue=sentinel):
                        self.assertEqual(got, expected)
    
    ##########
    # Search #
    ##########
    
    # TO DO
        

if __name__ == '__main__':
    unittest.main()