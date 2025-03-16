import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import time

class CoupledOscillatorNetwork:
    # ... existing code ...
    
    def __init__(self, n_oscillators=6, amplitude=1.0, frequency=1.0, mu=1.0):
        """Initialize the oscillator network."""
        self.n = n_oscillators
        self.amplitude = amplitude
        self.base_frequency = frequency
        self.omega = 2 * np.pi * frequency
        self.mu = mu
        
        # Initial state for all oscillators [x1, y1, x2, y2, ..., xn, yn]
        self.state = np.zeros(2 * self.n)
        for i in range(self.n):
            self.state[2*i] = 0.1  # Small initial x value
        
        # Coupling weights matrix (will be set based on gait)
        self.coupling_weights = np.zeros((self.n, self.n))
        self.phase_biases = np.zeros((self.n, self.n))
        
        # Added: track individual oscillator frequencies and amplitudes
        self.frequencies = np.ones(self.n) * frequency
        self.amplitudes = np.ones(self.n) * amplitude
        
        # Added: tracking current gait and direction
        self.current_gait = "tripod"
        self.direction_phase = 0.0  # 0 for forward, π for backward
        self.turning = False
        self.turning_direction = None
        self.turning_factor = 0.0
        
        self.last_update_time = time.time()
        
        # Default to tripod gait
        self.set_tripod_gait()
    
    def equations(self, state, t):
        """Differential equations for the coupled oscillator network."""
        derivatives = np.zeros_like(state)
        
        for i in range(self.n):
            x_i = state[2*i]
            y_i = state[2*i + 1]
            
            # Use individual oscillator frequencies and amplitudes
            local_omega = 2 * np.pi * self.frequencies[i]
            local_amplitude = self.amplitudes[i]
            
            # Uncoupled oscillator dynamics
            r_squared = x_i**2 + y_i**2
            dx_i = self.mu * (local_amplitude - r_squared) * x_i - local_omega * y_i
            dy_i = self.mu * (local_amplitude - r_squared) * y_i + local_omega * x_i
            
            # Add coupling terms
            for j in range(self.n):
                if i != j and self.coupling_weights[i, j] != 0:
                    x_j = state[2*j]
                    y_j = state[2*j + 1]
                    
                    # Calculate coupling based on phase difference
                    phase_bias = self.phase_biases[i, j]
                    coupling_term_x = x_j * np.cos(phase_bias) - y_j * np.sin(phase_bias)
                    coupling_term_y = x_j * np.sin(phase_bias) + y_j * np.cos(phase_bias)
                    
                    dx_i += self.coupling_weights[i, j] * (coupling_term_x - x_i)
                    dy_i += self.coupling_weights[i, j] * (coupling_term_y - y_i)
            
            derivatives[2*i] = dx_i
            derivatives[2*i + 1] = dy_i
        
        return derivatives
    
    def turn_right(self, turning_factor=0.3):
        """
        Configure the CPG to make the hexapod turn right.
        
        This works by:
        1. Increasing the stride length (amplitude) for left legs (1,3,5)
        2. Decreasing the stride length for right legs (0,2,4)
        3. Increasing the frequency for left legs
        4. Decreasing the frequency for right legs
        
        Args:
            turning_factor: How sharp the turn should be (0.0 to 1.0)
        """
        # Ensure turning factor is within bounds
        turning_factor = max(0.0, min(1.0, turning_factor))
        
        # Update tracking variables
        self.turning = True
        self.turning_direction = "right"
        self.turning_factor = turning_factor
        
        # Adjust amplitudes and frequencies for each leg
        for i in range(self.n):
            if i % 2 == 0:  # Right legs (0, 2, 4)
                # Reduce amplitude and frequency for right legs
                self.amplitudes[i] = self.amplitude * (1.0 - turning_factor * 0.5)
                self.frequencies[i] = self.base_frequency * (1.0 - turning_factor * 0.3)
            else:  # Left legs (1, 3, 5)
                # Increase amplitude and frequency for left legs
                self.amplitudes[i] = self.amplitude * (1.0 + turning_factor * 0.5)
                self.frequencies[i] = self.base_frequency * (1.0 + turning_factor * 0.3)
    
    def turn_left(self, turning_factor=0.3):
        """
        Configure the CPG to make the hexapod turn left.
        
        This works by:
        1. Increasing the stride length (amplitude) for right legs (0,2,4)
        2. Decreasing the stride length for left legs (1,3,5)
        3. Increasing the frequency for right legs
        4. Decreasing the frequency for left legs
        
        Args:
            turning_factor: How sharp the turn should be (0.0 to 1.0)
        """
        # Ensure turning factor is within bounds
        turning_factor = max(0.0, min(1.0, turning_factor))
        
        # Update tracking variables
        self.turning = True
        self.turning_direction = "left"
        self.turning_factor = turning_factor
        
        # Adjust amplitudes and frequencies for each leg
        for i in range(self.n):
            if i % 2 == 0:  # Right legs (0, 2, 4)
                # Increase amplitude and frequency for right legs
                self.amplitudes[i] = self.amplitude * (1.0 + turning_factor * 0.5)
                self.frequencies[i] = self.base_frequency * (1.0 + turning_factor * 0.3)
            else:  # Left legs (1, 3, 5)
                # Reduce amplitude and frequency for left legs
                self.amplitudes[i] = self.amplitude * (1.0 - turning_factor * 0.5)
                self.frequencies[i] = self.base_frequency * (1.0 - turning_factor * 0.3)
    
    def stop_turning(self):
        """
        Stop turning and reset to straight movement.
        """
        self.turning = False
        self.turning_direction = None
        self.turning_factor = 0.0
        
        # Reset all amplitudes and frequencies to base values
        for i in range(self.n):
            self.amplitudes[i] = self.amplitude
            self.frequencies[i] = self.base_frequency
    
    def set_backward(self, backward=True):
        """
        Set the robot to move backward.
        
        This inverts the phase relationships between all oscillators,
        effectively reversing the direction of the traveling wave.
        
        Args:
            backward: True to move backward, False to move forward
        """
        self.direction_phase = np.pi if backward else 0.0
        self._update_phase_relationships()
    
    def set_forward(self):
        """Convenience method to set forward movement."""
        self.set_backward(False)
    
    def _update_phase_relationships(self):
        """
        Update phase relationships based on current gait and direction.
        """
        # First reset to base gait
        if self.current_gait == "tripod":
            self.set_tripod_gait(reset_direction=False)
        elif self.current_gait == "wave":
            self.set_wave_gait(reset_direction=False)
        
        # Then apply direction phase if moving backward
        if self.direction_phase != 0:
            for i in range(self.n):
                for j in range(self.n):
                    if i != j:
                        self.phase_biases[i, j] = (self.phase_biases[i, j] + self.direction_phase) % (2 * np.pi)
    
    def set_tripod_gait(self, coupling_strength=1.0, reset_direction=True):
        """Set coupling weights and phase biases for tripod gait."""
        # Store current gait
        self.current_gait = "tripod"
        
        # Reset direction if requested
        if reset_direction:
            self.direction_phase = 0.0
        
        # Reset coupling matrices
        self.coupling_weights = np.zeros((self.n, self.n))
        self.phase_biases = np.zeros((self.n, self.n))
        
        # Tripod gait phase relationships
        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    self.coupling_weights[i, j] = coupling_strength
                    
                    # For tripod gait: 
                    # - Legs in same tripod: in phase (0)
                    # - Legs in different tripods: anti-phase (pi)
                    same_tripod = (i % 2) == (j % 2)
                    self.phase_biases[i, j] = 0 if same_tripod else np.pi
    
    def set_wave_gait(self, coupling_strength=1.0, reset_direction=True):
        """Set coupling weights and phase biases for wave gait."""
        # Store current gait
        self.current_gait = "wave"
        
        # Reset direction if requested
        if reset_direction:
            self.direction_phase = 0.0
        
        # Reset coupling matrices
        self.coupling_weights = np.zeros((self.n, self.n))
        self.phase_biases = np.zeros((self.n, self.n))
        
        # Wave gait phase relationships
        for i in range(self.n):
            for j in range(self.n):
                if i != j:
                    self.coupling_weights[i, j] = coupling_strength
                    
                    # For wave gait: phase difference = (2π/n) * (j-i)
                    phase_diff = (2 * np.pi / self.n) * ((j - i) % self.n)
                    self.phase_biases[i, j] = phase_diff