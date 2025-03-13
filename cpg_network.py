import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import time

class CoupledOscillatorNetwork:
    """
    A network of coupled Hopf oscillators for hexapod locomotion.
    
    This network models six legs with appropriate phase relationships
    for different gaits (e.g., tripod, wave, ripple).
    """
    def __init__(self, n_oscillators=6, amplitude=1.0, frequency=1.0, mu=1.0):
        """
        Initialize the oscillator network.
        
        Args:
            n_oscillators: Number of oscillators (typically 6 for hexapod)
            amplitude: Amplitude of oscillation
            frequency: Frequency of oscillation in Hz
            mu: Convergence rate
        """
        self.n = n_oscillators
        self.amplitude = amplitude
        self.omega = 2 * np.pi * frequency
        self.mu = mu
        
        # Initial state for all oscillators [x1, y1, x2, y2, ..., xn, yn]
        self.state = np.zeros(2 * self.n)
        for i in range(self.n):
            self.state[2*i] = 0.1  # Small initial x value
        
        # Coupling weights matrix (will be set based on gait)
        self.coupling_weights = np.zeros((self.n, self.n))
        self.phase_biases = np.zeros((self.n, self.n))
        
        self.last_update_time = time.time()
        
        # Default to tripod gait
        self.set_tripod_gait()
    
    def equations(self, state, t):
        """
        Differential equations for the coupled oscillator network.
        
        Args:
            state: Current state [x1, y1, x2, y2, ..., xn, yn]
            t: Time variable (required by odeint)
        
        Returns:
            Derivatives of the state
        """
        derivatives = np.zeros_like(state)
        
        for i in range(self.n):
            x_i = state[2*i]
            y_i = state[2*i + 1]
            
            # Uncoupled oscillator dynamics
            r_squared = x_i**2 + y_i**2
            dx_i = self.mu * (self.amplitude - r_squared) * x_i - self.omega * y_i
            dy_i = self.mu * (self.amplitude - r_squared) * y_i + self.omega * x_i
            
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
    
    def update(self, dt=None):
        """
        Update the network state by integrating over time dt.
        
        Args:
            dt: Time step for integration (if None, uses elapsed time since last update)
        
        Returns:
            Array of x-values for all oscillators
        """
        if dt is None:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
        
        # Integrate the system for one time step
        t = np.array([0, dt])
        state_trajectory = odeint(self.equations, self.state, t)
        
        # Update the state
        self.state = state_trajectory[-1]
        
        # Return x-values for all oscillators
        return np.array([self.state[2*i] for i in range(self.n)])
    
    def set_tripod_gait(self, coupling_strength=1.0):
        """
        Set coupling weights and phase biases for tripod gait.
        
        In tripod gait, legs are divided into two groups that move
        in alternation (legs 0, 2, 4 and legs 1, 3, 5).
        
        Args:
            coupling_strength: Strength of coupling between oscillators
        """
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
    
    def set_wave_gait(self, coupling_strength=1.0):
        """
        Set coupling weights and phase biases for wave gait.
        
        In wave gait, legs have sequential phase differences of 2π/n.
        This is more stable but slower than tripod gait.
        
        Args:
            coupling_strength: Strength of coupling between oscillators
        """
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
    
    def reset(self):
        """Reset the oscillator network."""
        self.state = np.zeros(2 * self.n)
        for i in range(self.n):
            self.state[2*i] = 0.1  # Small initial x value
        self.last_update_time = time.time()

# Demonstration code
if __name__ == "__main__":
    # Create a CPG network with 6 oscillators at 1Hz
    cpg = CoupledOscillatorNetwork(n_oscillators=6, frequency=1.0)
    
    # Simulate for 5 seconds with 100 points per second
    t = np.linspace(0, 5, 500)
    dt = t[1] - t[0]
    
    # Arrays to store the oscillator outputs
    outputs = np.zeros((len(t), cpg.n))
    
    # Simulate the oscillator network
    for i in range(len(t)):
        outputs[i] = cpg.update(dt)
    
    # Plot the results
    plt.figure(figsize=(14, 8))
    
    # Tripod gait
    plt.subplot(2, 1, 1)
    for i in range(cpg.n):
        plt.plot(t, outputs[:, i], label=f'Leg {i}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Tripod Gait CPG Output')
    plt.legend()
    plt.grid(True)
    
    # Reset and switch to wave gait
    cpg.reset()
    cpg.set_wave_gait()
    
    # Simulate wave gait
    wave_outputs = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        wave_outputs[i] = cpg.update(dt)
    
    # Wave gait
    plt.subplot(2, 1, 2)
    for i in range(cpg.n):
        plt.plot(t, wave_outputs[:, i], label=f'Leg {i}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Wave Gait CPG Output')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()