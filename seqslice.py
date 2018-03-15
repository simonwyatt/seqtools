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

from reversed import SeqReversible

class SeqSlice(SeqReversible):
    """
    Base class for smart slices of sequence types.
    
    This class implements index arithmetic to compute lengths, retrieve single items, and compose slices.
    Use cases:
        1.  Direct construction of lazy slices of explicit sequences (i.e. strings, lists, tuples).
        2.  Base class for sequence-specific slice classes, which can leverage additional facts about
            particular sequence classes to derive efficient implementations of e.g. __contains__, __iter__.
            In this situation a SeqSlice instance should always be obtained by slicing the pertinent object,
            never by invoking the SeqSlice constructor directly.
    
    Examples:
        >>> from string import ascii_lowercase
        >>> s = SeqSlice(ascii_lowercase, slice(2, None, 2))
        >>> s
        SeqSlice('abcdefghijklmnopqrstuvwxyz', slice(2, None, 2))
        >>> ''.join(s)
        'cegikmoqsuwy'
        >>> ascii_lowercase[2::2]
        'cegikmoqsuwy'
        >>> len(s)
        12
        
        >>> s2 = s[2::2]
        >>> s2
        SeqSlice('abcdefghijklmnopqrstuvwxyz', slice(6, None, 4))

        >>> ''.join(s2)
        'gkosw'
        >>> ascii_lowercase[6::4]
        'gkosw'
        >>> ascii_lowercase[2::2][2::2]
        'gkosw'
        >>> len(s2)
        5
        
        >>> s3 = SeqSlice(ascii_lowercase, slice(None, None, -3))
        >>> s3
        SeqSlice('abcdefghijklmnopqrstuvwxyz', slice(None, None, -3))
        >>> ''.join(s3)
        'zwtqnkheb'
        >>> ascii_lowercase[::-3]
        'zwtqnkheb'
        >>> s4 = s3[::2]
        >>> s4
        SeqSlice('abcdefghijklmnopqrstuvwxyz', slice(None, None, -6))
        >>> ''.join(s4)
        'ztnhb'
        >>> ascii_lowercase[::-3][::2]
        'ztnhb'
    """
    def __init__(self, seq, slice_):
        self.seq = seq
        try:
            L = len(self.seq)
        except OverflowError:
            L = self.seq.len()
        self._baselen = L
        self.slice = slice_
        self.i_start, self.i_stop, _ = slice_.indices(L)
    
    def len(self):
        start, stop, _ = self.slice.indices(self._baselen)
        return (abs(self.i_stop - self.i_start) - 1) // abs(self.slice.step) + 1
    def __len__(self):
        return self.len()
    
    def __getitem__(self, index):
        if isinstance(index, slice):
            if self.slice.start is None and index.start is None:
                start = None
            else:
                istart = index.start or (0 if index.step > 0 else self.len() - 1)
                start = self.i_start + istart * self.slice.step
                
            if index.stop is not None:
                stop  = self.i_start + index.stop * self.slice.step
            else:
                stop = self.slice.stop
            
            if self.slice.step is None and index.step is None:
                step = None
            else:
                step  = self.slice.step  * (index.step or 1)
            
            return type(self)(self.seq, slice(start, stop, step)) # Cooperate with subclasses.
        else:
            L = self.len()
            if not (-L <= index < L):
                raise IndexError("SeqSlice index out of range")
            return self.seq[self.i_start + index*self.slice.step]
    
    def _seqtools_reversed(self):
        start = start + (self.len() - 1) * self.slice.step
        stop = start - self.slice.step
        step = -self.slice.step
        return type(self)(self.seq, slice(start, stop, step))
    
    # __contains__, __iter__, __reversed__ use the inherited Sequence methods,
    # which just use __len__ and __getitem__ to traverse the list like a C array.
    # Most sequences can probably construct a more-efficient implementation.
    
    def __repr__(self):
        return "SeqSlice({}, {})".format(repr(self.seq), repr(self.slice))