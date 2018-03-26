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
    
    # Future: Consider overriding __new__ to just return the base sequence without allocating a new wrapper object
    # when using a trivial slice: step in (None, 1) and start in (None, 0, -L) and (stop is None or stop >= L)
    # Also could do something like
    # if isinstance(seq, SeqSliceable):
    #   return seq[slice_]
    # but we have to make sure that the seq type's SeqSlice subclass doesn't just recursively keep doing this
    # without ever allocating an instance.
    
    def _baselen(self):
        try:
            L = self._seq.len()
        except AttributeError:
            L = len(self._seq)
        return L
    
    def _bounds(self):
        return self._slice.indices(self._baselen())
    
    def len(self):
        # TODO: Verify. Possibly amenable to simplification.
        
        start, stop, step = self._bounds()
        # This normalizes start and stop to positive indices,
        # eliminating the need to reason by cases on their signs or on whether they are None.
        
        # Algorithm reproduced from CPython implementation of slicing for ranges.
        # See get_len_of_range in Objects/rangeobject.c of CPython
        if (step > 0 and start < stop) or (step < 0 and start > stop):
            return (abs(stop - start) - 1) // abs(step) + 1
        else:
            return 0
        
    def __len__(self):
        return self.len()
    
    def _compose_index(self, i):
        """
        Precondition:  `i` is an integer such that `-L <= i < L`, where `L = self.len()`.
        Postcondition:
            `self._compose_index(i)` is one of the two integers `j` such that `self[i] = self._seq[j]`.
            The sign of `j` is determined as follows:
            For nonnegative indices `i >= 0`, computed as offsets from the start of the slice:
                `j` is negative if `self` has a negative start, either explicitly or when start is None with a negative step,
                and positive otherwise.
            For negative indices `i < 0`, computed as offsets from the end of the slice:
                `j` is negative if `self` has a stop relative to the end of `self._seq`, either via an explicit negative stop
                    or when Stop is none with a positive step,
                and positive otherwise.
        
        Due to the weak precondition, the caller must do explicit bounds checking to determine whether `i`
        is in-bounds in `self`. Out-of-bounds values of `i` may e.g. produce indices in `self._seq` which are legal indices there,
        but go past the stop of `self`.
        """
        
        # We will calculate in the world of positive indices into the base sequence,
        # explicitly converting our answer to a negative number when necessary.
        start, stop, step = self._bounds()
        
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
        """
        Precondition:  `s` is a slice object.
        Postcondition: `self._compose_slice(s)` is a slice object `t` such that
            `self[s]` and `self._seq[t]` are elementwise equal as sequences.
        """
        # THIS IS HARDER TO GET RIGHT THAN YOU THINK.
        # Various combinations of negative indices and step sizes give rise to a lot of unintuitive corner cases.
                
        # Default to start, stop, step parameters of `self`, then use `s` to modify.
        start, stop, step = self._slice.start, self._slice.stop, self._slice.step
        
        # Compose step parameter:
        # If `s.step` is None, default to taking 1 step at a time through `self`,
        # which is by definition `self._slice.step` steps through `self._seq`,
        # which is what we already initialized `step` to, and we don't need to change it.
        if s.step is not None:
            if step is not None:
                # Each step through `self` is equivalent to `step` steps through `self._seq`,
                # and we're taking `s.step` steps at a time through `self`.
                step = step * s.step
            else:
                # `self` was using a step of None, which is implicitly a step of 1.
                step = s.step
        # But note that we don't use this value to reason about the `start` or `stop` parameters;
        # that's all based on the direction of traversal through `self` given by `s.step`.
        
        if s.start is not None or s.stop is not None:
            # We will be composing the start or stop parameter.
            # This requires bounds-checking using multiple occurrence of `self.len()`;
            # compute and save this value once now.
            L = self.len()
        
        # Compose start parameter:
        if s.start is not None:
            # Bounds-check the given value of `s.stop`
            if -L <= s.start < L: # In-bounds.
                # Use index arithmetic to obtain equivalent index into `self._seq`.
                start = self._compose_index(s.start)
            # If out-of-bounds, compare step direction to which boundary we're outside of and clip accordingly:
            elif ((s.start >= L and (s.step is     None or  s.step > 0))   # Start after  back  with positive step.
              or  (s.start < -L and (s.step is not None and s.step < 0))): # Start before front with negative step.
                # Slice starts too late to capture any elements.
                # Clip `start` to equal `stop`, forcing empty slice.
                start = stop
            # Otherwise, slice starts too early: clip `start` to `self._slice.start`,
            # its initial value, which we don't need to change.
        # If `s.start` is None, default behavior depends on the sign of `s.step`.
        # If `s.step` is None or positive, this is an implied start from the start of `self`,
        #   which is what we already initialized `start` to, and we don't need to change it.
        elif s.step is not None and s.step < 0:
            # This case is an implied start from the *end* of `self`, so
            start = self._compose_index(-1)
    
        # Compose stop parameter:
        # If `s.stop` is None, just keep going through `self._seq` until we run off the end of `self`,
        # which by definition is at `self._slice.stop`,
        # which is what we already initialized `stop` to, and we don't need to change it.
        if s.stop is not None:
            # Bounds-check the given value of `s.stop`:
            if -L <= s.stop < L: # The given `s.stop` actually lies within `self`.
                # Use index arithmetic to obtain equivalent index into `self._seq`.
                stop = self._compose_index(s.stop)
            # If out-of-bounds, compare step direction to which boundary we're outside of and clip accordingly:
            elif ((s.stop < -L and (s.step is     None or  s.step > 0))   # Stop before front with positive step.
              or  (s.stop >= L and (s.step is not None and s.step < 0))): # Stop after  back  with negative step.
                # Slice stops too early to capture any elements.
                # Clip `stop` to equal `start`, forcing an empty slice.
                stop = start
            # Otherwise, slice stops too late: clip `stop` to `self._slice.stop`,
            # its initial value, which we don't need to change.
        
        return slice(start, stop, step)
    
    def __getitem__(self, index):
        """
        Return `self[index]`.
        """
        if isinstance(index, slice):
            return type(self)(self._seq, self._compose_slice(index))
        else:
            # Check bounds before attempting index arithmetic; precondition of _compose_index requires this to happen here
            L = self.len()
            if not (-L <= index < L):
                raise IndexError("SeqSlice index out of range")
            
            return self._seq[self._compose_index(index)]
        # TODO: correctness arguments for all methods here, but especially this one!
    
    def _seqtools_reversed(self):
        return self[::-1]
    
    def __repr__(self):
        (start, stop, step) = (str(i) if i is not None else "" for i in (self._slice.start, self._slice.stop, self._slice.step))
        return "<{} {}[{}:{}:{}]>".format(type(self).__name__, repr(self._seq), start, stop, step)

if __name__ == "__main__":
    import doctest
    doctest.testmod()