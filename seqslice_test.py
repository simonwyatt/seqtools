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
    
    #@unittest.skip("not implemented")
    def test_sub_slice(self):
        """
        Check that slices of SeqSlice instances are new SeqSlice instances with
        correctly computed slice parameters.
        """
        # Start & stop positions for outer slices.
        starts_o = (None, 2, 10, -23, -15)
        stops_o  = (None, 6, 14, -19,  -6)
        
        # Start & stop positions for inner slices.
        starts_i = (None, 1,  4,  -8,  -4)
        stops_i  = (None, 3,  6,  -6,  -1)
        
        steps    = (None, 1, -1, 2, -3)
        
        breakpoint = (object(), object())
        #breakpoint = ((None, 6, None,), (-8, None, None))
        
        for args_o in itertools.product(starts_o, stops_o, steps):
            index_o = slice(*args_o)
            outer = SeqSlice(ascii_lowercase, index_o)
            for args_i in itertools.product(starts_i, stops_i, steps):
                if False and args_i[2] is not None and args_i[2] < 0:
                    continue # Skip subslices with negative steps for now
                
                index_i = slice(*args_i)
                if (args_o, args_i) == breakpoint:
                    import pdb; pdb.set_trace()
                
                inner = outer[index_i]
                
                expected = ascii_lowercase[index_o][index_i]
                result = ''.join(inner)
                
                try:
                    composed = (inner._slice.start, inner._slice.stop, inner._slice.step)
                except AttributeError: # fell back
                    composed = "<empty non-slice object>"
                
                with self.subTest(s1 = index_o, s2 = index_i, composed = composed):
                    self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()