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
    
    This class chiefly implements the `len`, `__len__`, and `__getitem__` methods, which rely on arithmetic
    independent of the type of the underlying class.
    
    `__contains__`, `__iter__`, `__reversed__`, `index`, and `count` fall back on the inherited methods
    from the Sequence ABC, which use `__len__` and `__getitem__` to traverse the underlying sequence
    one element at a time. Sequences that lazily construct elements as a function of indices, rather than
    explicitly storing arbitrarily elements, can likely implement these methods more efficiently.
    
    Examples:
        >>> from string import ascii_lowercase
        >>> s = SeqSlice(ascii_lowercase, slice(2, None, 2))
        >>> s
        <SeqSlice 'abcdefghijklmnopqrstuvwxyz'[2::2]>
        >>> ''.join(s)
        'cegikmoqsuwy'
        >>> ascii_lowercase[2::2]
        'cegikmoqsuwy'
        >>> len(s)
        12
        
        >>> s2 = s[2::2]
        >>> s2
        <SeqSlice 'abcdefghijklmnopqrstuvwxyz'[6::4]>

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
        <SeqSlice 'abcdefghijklmnopqrstuvwxyz'[::-3]>
        >>> ''.join(s3)
        'zwtqnkheb'
        >>> ascii_lowercase[::-3]
        'zwtqnkheb'
        >>> s4 = s3[::2]
        >>> s4
        <SeqSlice 'abcdefghijklmnopqrstuvwxyz'[::-6]>
        >>> ''.join(s4)
        'ztnhb'
        >>> ''.join(s3[1::2])
        'wqke'
        >>> ascii_lowercase[::-3][::2], ascii_lowercase[::-3][1::2]
        ('ztnhb', 'wqke')
    """
    def __init__(self, seq, slice_):
        self._seq = seq
        #try:
        #    L = seq.len()
        #except AttributeError:
        #    L = len(seq)
        #self._baselen = L
        self._slice = slice_
        #self.i_start, self.i_stop, self._step = slice_.indices(L)
    
    # TODO: override __new__ to return original sequence
    # when step in (None, 1) and start in (None, 0, -L) and (stop is None or stop >= L)
    
    def _baselen(self):
        try:
            L = self._seq.len()
        except AttributeError:
            L = len(self._seq)
        return L
    
    def _bounds(self):
        return self._slice.indices(self._baselen())
    
    def len(self):
        # Algorithm reproduced from CPython implementation of slicing for ranges.
        # See get_len_of_range in Objects/rangeobject.c of CPython
        # TODO: Verify. Possibly amenable to simplification.
        start, stop, step = self._bounds()
        if (step > 0 and start < stop) or (step < 0 and start > stop):
            return (abs(stop - start) - 1) // abs(step) + 1
        else:
            return 0
        
    def __len__(self):
        return self.len()
    
    def _compose_index(self, i):
        """
        Precondition:  `i` is an integer.
        Postcondition: If `i` is within the bounds of `self`,
            `self._compose_index(i)` is an integer `j` such that `self[i] = self._seq[j]`.
            The sign of `j` is determined as follows:
            For nonnegative indices `i >= 0`, computed as offsets from the start of the slice:
                `j` is negative if `self` has a negative start, either explicitly or when start is None with a negative step,
                and positive otherwise.
            For negative indices `i < 0`, computed as offsets from the end of the slice:
                ...
            If `i` is out of bounds in `self`, then `self._compose_index(i)` is outside the bounds of `self._seq`.
                (Consequently, `self[i]` will raise IndexError if and only if `self._seq[j]` does.)
        """
        
        # We will temporarily work in the world of positive indices into the base sequence,
        # converting our answer to a negative number when necessary.
        start, stop, step = self._bounds()
        """_, _, step = self._bounds()
        
        start = self._slice.start
        if start is None:
            if step > 0:
                start = 0
            else:
                start = -1
        
        stop = self._slice.stop
        if stop is None:
            L = self._baselen()
            if step > 0:
               stop = (start - L) % step + L
            else:
                stop = L - (L - start) % step"""
        
        if i >= 0:
            # Nonnegative indices are computed as offsets from the start position:
            j = start + i * step
            # Recall that the positive index for `start` has been taken regardless of the actual sign;
            # so that we can explicitly control the sign of the return value:
            # We give the negative solution when this slice is given with a negative start position,
            # either explicitly, or by using start = None with a negative step size (implicit start = -1).
            if ((self._slice.start is not None and self._slice.start < 0)
            or  (self._slice.start is     None and step < 0)):
                j -= self._baselen()
        else:
            # Negative indices are computed as offsets from a "base" position, roughly the "index after the last index".
            
            # With a positive step size (either explicitly or step = None), `base` is the smallest integer such that
            #   stop <= base and base % step == start % step.
            # From the extremal choice of `base` as the smallest such value, we obtain a second constraint
            #   stop <= base < stop + step.
            # Subtracting `stop` from each constraint,
            #   0 <= base - stop < step
            #   (base - stop) % step == (start - stop) % step
            # The inequality tells us that (base - stop) % step == base - stop; substituting & rearranging,
            base = (start - stop) % step + stop
            
            # With a negative step size, `base` is the largest integer such that
            #   base <= stop and base % step == start % step.
            # Proceeding much as in the preceding case,
            #   stop + step < base        <= stop
            #          step < base - stop <= 0,
            # which tells us once again that (base - stop) % step == base - stop
            # (recall that `x % step` produces the negative solution when step < 0)
            # so the same formula remains correct.
            
            # Now take an offset from the computed base value.
            j = base + i * step
            # This will always be a positive index, since with i < 0, step < 0 this gives
            #   j >= base - step
            #   stop < base - step <= stop - step
            # and we earlier took the positive for `stop`.

            # Give the negative solution when this slice is given with a stop position
            # relative to the end of the underlying sequence,
            # either with an explicit negative stop parameter,
            # or by using stop = None with a positive step size.
            if ((self._slice.stop is not None and self._slice.stop < 0)
            or  (self._slice.stop is     None and step > 0)):
                j -= self._baselen()
        return j
        
    def _compose_slice(self, s):
        start, stop, step = self._slice.start, self._slice.stop, self._slice.step
        
        if s.step is not None:
            step = step * s.step if step is not None else s.step
            
        #if step is None or step > 0:        
        if s.start is not None:
            start = self._compose_index(s.start)
            """if start < 0: # Negative return value from `_compose_index` indicates start before
                          # beginning of underlying sequence, not at index from right!
                if step is None or step > 0: # Forward step: start at beginning.
                    start = 0
                else: # Reverse step: Push all the way out of bounds
                    start -= -self._baselen"""
            # if start >= self._baselen: Above-bounds indices handled correctly by default behavior of slicing
    
        if s.stop is not None:
            i_stop = self._compose_index(s.stop)
            L = self._baselen()
            if stop is not None:
                new = i_stop % L
                old =   stop % L
            if (stop is None
                    or ((step is None or step > 0) and new < old)
                    or ((step is not None and step < 0) and new > old)
               ):
                stop = i_stop
        
        return slice(start, stop, step)
    
    def __getitem__(self, index):
        """
        Return `self[index]`.
        """
        if isinstance(index, slice): # Compose slices.
            if False:
                # Compute start position of composed slice:
                if self.slice.start is None and index.start is None:
                    # Neither composed slice wishes to override the default start position
                    # corresponding to the computed step size.
                    start = None
                else:
                    # Start at what index into this slice?
                    istart = index.start or (0 if index.step > 0 else self.len() - 1)
                    # If none given, default to end corresponding to given step size.
                    # The corresponding index 
                    start = self._compose_index( istart )
                
                if index.stop is not None:
                    stop = self._compose_index ( index.stop )
                else:
                    stop = self.slice.stop
            
                if self.slice.step is None and index.step is None:
                    step = None
                else:
                    step  = self._step  * (index.step or 1)
            
                return type(self)(self.seq, slice(start, stop, step)) # Cooperate with subclasses.
            return type(self)(self._seq, self._compose_slice(index))
        else:
            L = self.len()
            if not (-L <= index < L):
                raise IndexError("SeqSlice index out of range")
            return self._seq[self._compose_index(index)]
        # TODO: correctness arguments for all methods here, but especially this one!
    
    def _seqtools_reversed(self):
        return self[::-1]
        #start = start + (self.len() - 1) * self.slice.step
        #stop = start - self.slice.step
        #step = -self.slice.step
        #return type(self)(self.seq, slice(start, stop, step))
    
    def __repr__(self):
        (start, stop, step) = (str(i) if i is not None else "" for i in (self._slice.start, self._slice.stop, self._slice.step))
        return "<{} {}[{}:{}:{}]>".format(type(self).__name__, repr(self._seq), start, stop, step)

if __name__ == "__main__":
    import doctest
    doctest.testmod()