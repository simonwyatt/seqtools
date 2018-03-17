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

from collections.abc import Sequence
from abc import abstractmethod

class SeqReversible(Sequence):
    """
    Abstract Base Class for a Sequence that provides its own conversion to a
    sequence with order reversed, overriding the default behavior of the `Reversed` class.
    
    A Sequence class should only inherit from SeqReversible if it can be reversed
    in some way more efficient than making an explicit copy or iterating over indices
    in reverse order.
    """
    @abstractmethod
    def _seqtools_reversed(self):
        """
        Return a sequence with the same elements as `self` in reversed order.
        """
        raise NotImplementedError

class Reversed(SeqReversible):
    """
    Precondition:  `seq` is a sequence.
    Postcondition: `Reversed(seq)` is a sequence that contains the same elements as `seq`
    in reversed order.
    
    This is particularly useful for virtual large sequences that construct a lot of elements
    lazily from indices without storing them all in memory.
    
    Comparison to builtin approaches:
        `reversed(iter)` returns an iterable, which in particular can't compute its length
        or do membership testing.
        Obtaining a reversed sequence with the slice [::-1] preserves the type of e.g. lists,
        which we may not want if `seq` is very large.
    
    Examples:    
        >>> Reversed(range(20, 30, 3))
        range(29, 17, -3)
    
        >>> Reversed('abcdefghij')[0]
        'j'
    
        >>> Reversed('abcdefghij')[9]
        'a'
    
        >>> Reversed('abcdefghij')[1::2]
        'igeca'
    
        >>> Reversed('abcdefghij')[-2:-5:-1]
        'bcd'
    
        >>> Reversed(Reversed('abcdefghij'))
        'abcdefghij'
    """
    def __new__(cls, seq):
        """
        Create a reversed sequence.
        
        Precondition:  `seq` is a sequence.
        Postcondition: `Reversed(seq)` is a sequence with `seq`'s elements in reverse order.
            This need not be a `Reversed` object; specifically,
                1. If `seq` is a range object, `Reversed(seq)` is `seq[::-1]`.
                2. If `seq` is an instance of the `SeqReversible` ABC,
                   `Reversed(seq)` is `seq._seqtools_reversed()`.
                3. Otherwise, `seq` is a `Reversed` object, which is simply a view of `seq`
                   with indices reversed.
        """
        # If given sequence is naturally reversible to some sequence of the same type,
        # return that instead of creating a Reversed object
        if isinstance(seq, range):
            return seq[::-1] #ranges do the right thing by default
        elif isinstance(seq, SeqReversible):
            return seq._seqtools_reversed()
        else:
            return super(Reversed, cls).__new__(cls)

    def __init__(self, seq):
        self._seq = seq
    
    def _revindex(self, i):
        return -1 - i
    
    def _revslice(self, s):
        start, stop, step = None, None, -1
        
        if s.step is not None:
            step = -s.step
        if s.start is not None:
            start = self._revindex(s.start)
        if s.stop is not None:
            stop = self._revindex(s.stop)
        
        return slice(start, stop, step)
    
    #Subscripting and searching: delegate to base sequence via index arithmetic.
    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._seq[self._revslice(index)]
        else:
            return self._seq[self._revindex(index)]
    def index(self, item, start=0, stop=None):
        if stop is None:
            stop = self.len()
        return self._revindex(self._seq.index(item, self._revindex(start), self._revindex(stop)))
        
    # Length & membership testing: delegate to base sequence.
    def __contains__(self, item):
        return item in self._seq
        # Correctness argument: `Reversed(seq)` must contain precisely the same
        #     elements as `seq` to satisfy the specification of `Reversed`.
    def count(self, item):
        return self._seq.count(item)
    
    # Correctness argument: The length of a sequence is invariant under reversal.
    def __len__(self):
        return len(self._seq)
    def len(self):
        try: #use overflow-safe len method if available,
            return self._seq.len()
        except AttributeError: #else fall back on builtin len
            return len(self._seq)
    
    #Iteration: delegate to the base sequence with order interchanged.
    def __iter__(self):
        return reversed(self._seq)
    def __reversed__(self):
        return iter(self._seq)
    
    def _seqtools_reversed(self):
        """Reverse a `Reversed` instance by extracting its underlying sequence."""
        return self._seq
    
    def __repr__(self):
        return "Reversed({})".format(repr(self._seq))

if __name__ == "__main__":
    import doctest
    doctest.testmod()