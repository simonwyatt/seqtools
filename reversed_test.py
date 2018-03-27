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
    
    ################
    # Construction #
    ################
    
    def test_of_range(self):
        """
        Check that calling `Reversed(seq)` when `seq` is a range
        produces another range with parameters modified appropriately.
        """
        # Coverage: Reversed.__new__ (first branch)
        cases = ((100,), (5, 10), (20, 40, 3), (0, -100, -1), (20, -21, -5))
        for args in cases:
            r = range(*args)
            with self.subTest(case=r):
                self.assertEqual(Reversed(r), r[::-1])
    
    def test_double_reverse(self):
        """
        Check that Reversing a `Reversed` object "cancels out" and extracts the underlying sequence.
        """
        # Coverage: Reversed.__new__ (second branch), Reversed._seqtools_reversed.
        self.assertIs(Reversed(self.r_alpha), alpha)
    
    def test_revinst(self):
        """
        Check that calling `Reversed(seq)` when `seq` is a built-in explicit sequence (eg string)
        produces a `Reversed` instance as desired.
        """
        # Coverage: Reversed.__new__ (third branch), Reversed.__init__
        self.assertIsInstance(self.r_alpha, Reversed)
        self.assertEqual(self.r_alpha._seq, alpha)
    
    ##########
    # Length #
    ##########
    
    def test_len(self):
        """
        Check that sequence length is invariant under reversal.
        """
        # Coverage: Reversed.__len__, Reversed.len (`except` branch)
        self.assertEqual(len(alpha), len(self.r_alpha))
        self.assertEqual(len(alpha), self.r_alpha.len())
        
    def test_len_huge(self):
        # Coverage: Reversed.len (`try` branch)
        from combinatorics import Product
        huge = Product(range(10**6), repeat=10)
        r_huge = Reversed(huge)
        self.assertEqual(r_huge.len(), 10**60)
    
    ###############
    # Item access #
    ###############
    
    def test_get_one_item(self):
        """
        Check that `Reversed.__getitem__` conforms to its specification when accessing valid single indices.
        """
        # Coverage: Reversed.__getitem__ (single index branch, index in bounds), Reversed._revindex
        cases = ( # First & last two items, plus an arbitrary item from the middle of the sequence,
                  # accessed at both positive & negative indices.
                  # Expected values computed by explicitly constructing string.ascii_lowercase[::-1].
            (  0, 'z'),
            (-26, 'z'),
            (  1, 'y'),
            (-25, 'y'),
            ( 24, 'b'),
            ( -2, 'b'),
            ( 25, 'a'),
            ( -1, 'a'),
            (  7, 's'),
            (-19, 's')
        )
        for index, expected in cases:
            with self.subTest(index=index):
                self.assertEqual(self.r_alpha[index], expected)
    
    def test_get_bad_item(self):
        """
        Check that `Reversed.__getitem__` raises IndexError when attempting to get invalid indices.
        """
        # Coverage: Reversed.__getitem__ (single index branch, index out of bounds),
        #           Reversed._revindex
        cases = (26, -27) # Positive & negative indices beyond limits of sequence.
        for index in cases:
            with self.subTest(index=index):
                with self.assertRaises(IndexError):
                    self.r_alpha[index]
    
    def test_slicing(self):
        """
        Check that `Reversed.__getitem__` conforms to its specification when accessing valid slices.
        """
        # Coverage: Reversed.__getitem__ (slice branch), Reversed._revslice (all branches, nonzero step),
        #           Reversed._revindex
        cases = ( # Computed from string.ascii_lowercase
            # Trivial slice
            ((None, None, None), "zyxwvutsrqponmlkjihgfedcba"),
            # Slices specifying only start position: inside & outside the sequence.
            ((   3, None, None),    "wvutsrqponmlkjihgfedcba"),
            ((  -3, None, None),                        "cba"),
            ((  99, None, None),                           ""),
            (( -99, None, None), "zyxwvutsrqponmlkjihgfedcba"),
            # Slices specifying only  stop position: inside & outside the sequence.
            ((None,    3, None), "zyx"                       ),
            ((None,   -3, None), "zyxwvutsrqponmlkjihgfed"   ),
            ((None,   99, None), "zyxwvutsrqponmlkjihgfedcba"),
            ((None,  -99, None),                           ""),
            # Slices specifying start & stop positions:
            # Start & stop in correct or inverted order, same or opposite signs.
            ((   3,    6, None),    "wvu"                    ),
            ((   6,    3, None),                           ""),
            ((   5,    2,   -1),    "uvw"                    ),
            ((   2,    5,   -1),                           ""),
            ((  -6,   -3, None),                     "fed"   ),
            ((  -3,   -6, None),                           ""),
            ((  -4,   -7,   -1),                     "def"   ),
            ((   3,   -3, None),    "wvutsrqponmlkjihgfed"   ),
            ((  -3,    3, None),                           ""),
            # Negative slices
            ((   2, None,   -1), "xyz"                       ),
            ((  -4, None,   -1),    "defghijklmnopqrstuvwxyz"),
            # With negative step, stop of -1 means "entire sequence is out of bounds" & returns nothing
            #   NOT "count down til first element & stop", returning whole sequence.
            ((None,   -1,   -1),                           ""),
            # Positive & negative larger steps.
            ((None, None,    4), "z"+"v"+"r"+"n"+"j"+"f"+"b" ),
            ((   1, None,    4),  "y"+"u"+"q"+"m"+"i"+"e"+"a"),
            ((  -3, None,   -4),   "c"+"g"+"k"+"o"+"s"+"w"   ),
            # Extremely large step, only start item retrieved.
            ((None, None,   99), "z"                         ),
        )
        for sliceargs, expected in cases:
            index = slice(*sliceargs)
            with self.subTest(index=index):
                self.assertEqual(''.join(self.r_alpha[index]), expected)
        
    def test_bad_slice(self):
        """
        Check that `Reversed.__getitem__` raises ValueError when attempting a slice with step size zero.
        """
        # Coverage: still Reversed.__getitem__, Reversed._revslice (zero step)
        step0 = slice(None, None, 0)
        with self.assertRaises(ValueError):
            self.r_alpha[step0]
    
    #############
    # Iteration #
    #############
    
    def test_iter(self):
        """
        Check that a forward iterator over a sequence `iter(seq)` produces the same items
        in the same order as  a reversed iterator over the reversed sequence
        `reversed(Reversed(seq))` and vice versa.
        """
        # Coverage: Reversed.__iter__, Reversed.__reversed_
        with self.subTest("iter"):
            for a, b in zip(reversed(alpha), iter(self.r_alpha)):
                self.assertEqual(a, b)
        with self.subTest("reversed"):
            for a, b in zip(iter(alpha), reversed(self.r_alpha)):
                self.assertEqual(a, b)
    
    ##########
    # Search #
    ##########
    
    def test_contains(self):
        """
        Check that item containment is invariant under reversal:
        `Reversed(seq)` contains precisely the same items as `seq`.
        """
        for c in string.printable:
            with self.subTest(c=c):
                self.assertEqual(c in alpha, c in self.r_alpha)
    
    def test_index(self):
        """
        Check that `Reversed.index` conforms to its specification.
        """
        s = "abcdefghij" * 5 # Multiple of a string creates numerous occurrence of elements,
                             # allowing us to exercise the `start` and `stop` parameters of `index`.
        s_r = Reversed(s)
        
        with self.subTest("no extra args"):
            self.assertEqual(s_r.index('e'), 5)
        
        # Start arg only
        for i in range(0, 46, 5):
            with self.subTest(start=i):
                self.assertEqual(s_r.index('e', i), (i+ 4)//10 * 10 + 5)
        for i in range(-5, -51, -5):
            with self.subTest(start=i):
                self.assertEqual(s_r.index('e', i), (i+54)//10 * 10 + 5)
        # Functions generating expected values computed from the fact
        # that 'e' occurs at index 5 in `s_r` and recurs
        # every 10 items thereafter until index 45.
        
        # Start arg only, past last occurrence so search should fail.
        with self.subTest(start=46):
            with self.assertRaises(ValueError):
                s_r.index('e', 46)
        
        # Start and stop args:
        # Focus on boundaries of interval between two successive occurences.
        foundCases = (
            (5, 15, 5), # Find occurrence at index 5.
            (5, 16, 5), # Expand search to encompass occurrence at index 15,
                        # but still find the occurrence at index 5 because it's first.
            (6, 16, 15) # Restrict search to exclude occurrence at index 5;
                        # now we find the occurrence at index 15.
        )
        for i, j, k in foundCases:
            with self.subTest(start=i, stop=j):
                self.assertEqual(s_r.index('e', i, j), k)
        # Specified failures:
        raiseCases = (
            (50,  0), # Start and stop in reversed order, search empty slice.
            ( 0,  4), # Search stops before first occurrence.
            ( 6, 15)  # Search strictly between occurrences at indices 5 and 15.
        )
        for i, j in raiseCases:
            with self.subTest(start=i, stop=j):
                with self.assertRaises(ValueError):
                    s_r.index('e', i, j )
    
    def test_count(self):
        """
        Check that number of occurrences of each item is invariant under reversal:
        For any item `x`, `Reversed(seq)` contains the same number of occurrences of `x`
        as `seq` (perhaps zero).
        """
        s = ''.join(alpha[i:i+5] for i in range(len(alpha)-4))
        r_s = Reversed(s)
        for c in string.printable:
            with self.subTest(c=c):
                self.assertEqual(r_s.count(c), s.count(c))

if __name__ == '__main__':
    unittest.main()