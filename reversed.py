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
    @abstractmethod
    def _seqtools_reversed(self):
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
        Slicing with [::-1] preserves the type of e.g. lists, which we may not want if `seq`
        is very large.
    
    Construction:
        The builtin `range` class knows how to reverse itself in an efficient way,
        and correspondingly, if `seq` is a range then `Reversed(seq) == seq[::-1]`
    
        If `seq` claims to know how to reverse itself by providing the `_seqtools_reversed` method
        of the `SeqReversible` ABC, then likewise `Reversed(seq) == seq._seqtools_reverse()`.
    
        Otherwise, `Reversed(seq)` creates a `Reversed` instance, which is a subscript-rewriting
        wrapper around `seq`. (Nested applications cancel.)
    
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
    
    def _revslice(self, s):
        start, stop, step = None, None, -1
        
        if s.step is not None:
            step = -s.step
        if s.start is not None:
            start = -1 - s.start
        if s.stop is not None:
            stop = -1 - s.stop
        
        return slice(start, stop, step)
    
    #Subscripting: delegate to base sequence via index arithmetic.
    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._seq[self._revslice(index)]
        else:
            return self._seq[-1 - index]
    
    #Length & membership testing: delegate to base sequence.
    def __len__(self):
        return len(self._seq)
    def len(self):
        return self._seq.len()
    def __contains__(self, item):
        return item in self._seq
    
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