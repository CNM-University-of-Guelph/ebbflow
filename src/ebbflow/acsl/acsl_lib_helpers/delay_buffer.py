import hashlib

import numpy as np

class DelayBuffer:
    def __init__(self, nmx, ic, initial_time=0.0):
        self.max_size = 2 * nmx
        self.buffer = np.zeros((self.max_size, 2), dtype=float)
        self.head = 0 # Pointer to the oldest element
        self.tail = 0 # Pointer to the next insertion point
        self.current_size = 0 # Current number of elements in the buffer
        self.ic = ic
        self.initial_time = initial_time
        
        # Pre-fill buffer with initial condition extending back in time
        # This represents "all past history" as per ACSL specification
        # Space initial times going backwards from initial_time
        # Using a reasonable spacing (could be adjusted based on expected delmin)
        time_spacing = 0.01
        self.buffer[:, 1] = ic
        self.buffer[:, 0] = np.linspace(
            initial_time - (self.max_size - 1) * time_spacing,
            initial_time,
            self.max_size
        )

        self.actual_data_points = 0  # Track real simulation data points

    def add(self, current_time, value):
        """Add a new (time, value) pair to the circular buffer."""
        self.buffer[self.tail, 0] = current_time
        self.buffer[self.tail, 1] = value
        self.tail = (self.tail + 1) % self.max_size
        
        if self.actual_data_points < self.max_size:
            self.actual_data_points += 1
        else:
            # Buffer is full, head advances as tail wraps around
            self.head = (self.head + 1) % self.max_size

    def get_delayed_value(self, current_time, tdl):
        """Get delayed value using linear interpolation."""
        if tdl <= 0:
            raise ValueError("Delay time (tdl) must be greater than 0")
        
        required_past_time = current_time - tdl

        # Handle initial condition period
        # If we're asking for a time before we have actual data, return ic
        if self.actual_data_points == 0:
            return self.ic
            
        # Get the appropriate time and value arrays
        if self.actual_data_points < self.max_size:
            # Buffer hasn't wrapped yet - use initial conditions + actual data
            # Initial conditions are in buffer[0:max_size-actual_data_points]
            # Actual data is in buffer[max_size-actual_data_points:max_size]
            ic_end = self.max_size - self.actual_data_points
            times = self.buffer[:, 0]  # All times (ic + actual)
            values = self.buffer[:, 1]  # All values (ic + actual)
            earliest_actual_time = self.buffer[ic_end, 0] if self.actual_data_points > 0 else float('inf')
        else:
            # Buffer has wrapped - only actual data
            times = np.concatenate((self.buffer[self.head:, 0], self.buffer[:self.head, 0]))
            values = np.concatenate((self.buffer[self.head:, 1], self.buffer[:self.head, 1]))
            earliest_actual_time = times[0]
        
        # If required time is before any actual data, return ic
        if required_past_time < earliest_actual_time and self.actual_data_points < self.max_size:
            return self.ic
            
        # If required time is before earliest available data (insufficient data case)
        if required_past_time < times[0]:
            raise RuntimeError(
                f"Not enough data points in delay buffer for tdl={tdl}. "
                f"Required time {required_past_time} is before earliest available data {times[0]}."
            )

        # Find the indices that bracket the required_past_time
        idx = np.searchsorted(times, required_past_time, side="right")
        
        if idx == 0:
            return values[0]
            
        if idx == len(times):
            return values[-1]

        # Linear interpolation between bracketing points
        t1, x1 = times[idx - 1], values[idx - 1]
        t2, x2 = times[idx], values[idx]
        
        if t2 == t1:  # Avoid division by zero
            return x1
            
        interpolated_value = x1 + (x2 - x1) * ((required_past_time - t1) / (t2 - t1))
        return interpolated_value
