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
        """
        Initialize Reversed instance `self`.
        
        Abstraction function: The sequence `seq` in reversed order is simply represented by a reference to `seq`;
            the methods of the Reversed class access this reference in reversed order.
        Representation invariant: 
        """
        self._seq = seq
    
    def _revindex(self, i):
        """
        Reverse an index.
        
        Precondition:  `i` is an integer.
        Postcondition: `self._revindex(i)` is the item at position `i` in `self._seq`,
        counting backwards from the end of `self._seq`.
        """
        # Correctness argument:
        # Using the definition of negative indices in Python sequences, let `self._seq` be the sequence
        #   (s[-L], s[-L+1], ..., s[-2], s[-1]).
        # The mapping i -> -1 - i maps the indices 0, 1, ..., L-2, L-1 to -1, -2, ..., -L+1, -L,
        # accessing the elements of `self._seq` in reverse order as desired.
        return -1 - i
    
    def _revslice(self, s):
        """
        Reverse a slice.
        
        Precondition:  `s` is a slice instance.
        Postcondition: `self._revslice(s)` is a slice object having the property that
            self._seq[self._revslice(s)] == self._seq[::-1][s]
        """
        # Correctness argument:
        start, stop, step = None, None, -1
        # If step size is not supplied, `self._seq` should be traversed with step size -1
        # to implement the usual default step size of 1 through a reversed view of `self._seq`.
        
        if s.step is not None:
            step = -s.step
            # If a step size is supplied, then taking this size of step through the reversed sequence
            # is equivalent to taking the opposite step through the original sequence.
        if s.start is not None:
            start = self._revindex(s.start)
            # Position `s.start` in the reversed sequence is equivalent to this position in the original sequence
            # by the specification of _revindex.
            # If no starting position is supplied, the default behavior is to start from whichever end of the
            # sequence is appropriate given the step size, so the negated step size correctly reverses the starting position.
        if s.stop is not None:
            stop = self._revindex(s.stop)
            # Same argument as for `start`, mutatis mutandis.
        
        # So `start`, `stop`, `step` are all now correct to slice `self._seq` in the correct way.
        return slice(start, stop, step)
    
    # Subscripting and searching: delegate to base sequence via index arithmetic.
    def __getitem__(self, index):
        """
        Compute self[index].
        
        Precondition:  `index` is an integer (-self.len() <= index < self.len) or slice object.
        Postcondition: `self[index]` is the item that would be obtained by `self._seq[index]`
            if `self._seq` was indexed in reversed order, i.e.
            self[index] == self._seq[::-1][index].
        """
        # Correctness argument: By division into cases.
        # Each of the functions `_revslice` and `_revindex` specify that they return the correct index
        # to obtain the desired results by subscripting `self._seq`.
        if isinstance(index, slice):
            return self._seq[self._revslice(index)]
        else:
            return self._seq[self._revindex(index)]
    
    def index(self, item, start=0, stop=None):
        """
        Return the least positive integer `i` such that `self[i] == item`
        and `self[i]` is contained in the slice `self[start:stop]`.
        Raise ValueError if no such integer exists.
        """
        
        # If no `stop` parameter provided, stop at the end of the sequence.
        if stop is None:
            stop = self.len()
            
        if hasattr(self._seq, "rindex"): # Underlying sequence supports reversed index search --
                                         # More efficient than squeezing whole search algorithm through Reversed wrapper
            # Compute start position of search in underlying sequence: Based on end position of reversed search
            rstart = self._revindex(stop) + 1
            # +1 to exclude the reversed `stop` position from being searched,
            # since it reverses to the (included) `start` position in the reversed search.
            
            # Compute stop position in underlying sequence from start position of reversed search:
            if start == 0:
                rstop = self.len()
                # In this case the last index to be searched is -1.
                # So adding 1 produces 0 and incorrectly stops the search before it starts!
                # Instead specify a positive `stop` position just above the end of the underlying sequence.
            else:
                rstop = self._revindex(start) + 1
                # +1 to keep searching & include the reversed `start` position in the search,
                # since it reverses to the (excluded) `stop` position in the reversed search.
            
            # Use `rindex` to search underlying sequence, then reverse that index to obtain the corresponding index in `self`.
            # But `_revindex` gives the negative solution and we specified the positive, so correct by adding `self.len()`.
            index = self._revindex(self._seq.rindex(item, rstart, rstop)) + self.len()
            
            return index
        else: # Fall back on default Sequence implementation -- this gets & checks items one at a time
            # Correctness follows from correctness of __getitem__
            super().index(item, start, stop)
        
    # Membership testing & counting: Invariant under reversal.
    def __contains__(self, item):
        return item in self._seq
        # Correctness argument: `Reversed(seq)` must contain precisely the same
        #     elements as `seq` to satisfy the specification of `Reversed`.
    def count(self, item):
        return self._seq.count(item)
        # Correctness argument: Per spec of `Reversed`,
        # number of occurrences of `item` in `Reversed(seq)` must equal that in `seq`.
    
    # Length: Invariant under reversal.
    def __len__(self):
        return len(self._seq)
    def len(self):
        try: #use overflow-safe len method if available,
            return self._seq.len()
        except AttributeError: #else fall back on builtin len
            return len(self._seq)
    
    # Iteration: delegate to the base sequence with order interchanged.
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