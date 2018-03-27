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

"""Unit tests for the `seqslice` module and its `SeqSlice` class."""

import unittest, itertools
from seqslice import SeqSlice
from string import ascii_lowercase

class TestSeqSlice(unittest.TestCase):
    def setUp(self):
        self.startstops = (None, 3, -3, 6, -6, 20, -20, 99, -99)
        self.steps = (None, 1, -1, 3, -3, 99, -99)

    def test_one_slice(self):
        """
        Check that SeqSlice instances produce the correct items,
        by comparison to ordinary explicit slices.
        """
        # Coverage: __init__, len, __len, __getitem__ (single item branch), internals e.g. _compose_index
        for sliceargs in itertools.product(self.startstops, self.startstops, self.steps):
            index = slice(*sliceargs)
            instance = SeqSlice(ascii_lowercase, index)
            expected = ascii_lowercase[index]
            with self.subTest(index=index):
                # Length matches.
                self.assertEqual(len(instance), len(expected))
                
                # Items are the same at all in-bounds indices.
                for i in range(-len(expected), len(expected)):
                    with self.subTest(pos=i):
                        self.assertEqual(instance[i], expected[i])
                
                # Boundaries are at the expected locations.
                for bad_i in (-len(expected) - 1, len(expected)):
                    with self.subTest(pos = bad_i):
                        with self.assertRaises(IndexError):
                            instance[bad_i]
                
                # Iteration produces the correct items.
                self.assertEqual(''.join(instance), expected)
    
    def test_sub_slice(self):
        """
        Check that slices of SeqSlice instances are new SeqSlice instances with
        correctly computed slice parameters.
        """
        # Coverage: Principally __getitem__ (slice branch), _compose_slice
        
        # Start & stop positions for outer slices.
        starts_o = (None, 2, 10, -23, -15)
        stops_o  = (None, 6, 14, -19,  -6)
        
        # Start & stop positions for inner slices.
        starts_i = (None, 1,  4,  -8,  -4)
        stops_i  = (None, 3,  6,  -6,  -1)
        
        steps    = (None, 1, -1, 2, -3)
        
        for args_o in itertools.product(starts_o, stops_o, steps):
            index_o = slice(*args_o)
            outer = SeqSlice(ascii_lowercase, index_o)
            for args_i in itertools.product(starts_i, stops_i, steps):
                index_i = slice(*args_i)
                inner = outer[index_i]
                
                expected = ascii_lowercase[index_o][index_i]
                
                try:
                    composed = (inner._slice.start, inner._slice.stop, inner._slice.step)
                except AttributeError: # fell back
                    composed = "<empty non-slice object>"
                
                with self.subTest(s1 = index_o, s2 = index_i, composed = composed):
                    # Length matches
                    L = len(expected)
                    self.assertEqual(len(inner), L)
                    
                    # Items the same at selected in-bounds indices
                    for i in (-L, -1, 0, 1, L - 1):
                        if -L <= i < L: # Not all of these indices will be in bounds for all subslices,
                                        # (e.g., sometimes inner is expected to be empty)
                                        # so only test the ones that are.
                            with self.subTest(pos=i):
                                self.assertEqual(inner[i], expected[i])
                    
                    # Boundaries at expected locations
                    for bad_i in (-L - 1, L):
                        with self.subTest(pos = bad_i):
                            with self.assertRaises(IndexError):
                                inner[bad_i]
                    
                    # Iteration produces the correct items
                    self.assertEqual(''.join(inner), expected)
    
    ########################################################
    # Iteration, searching: Correctness implied by that of #
    # __len__, __getitem__, and collections.abc.Sequence   #
    ########################################################

if __name__ == '__main__':
    unittest.main()