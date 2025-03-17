import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import time

class CoupledOscillatorNetwork:
    """
    A network of coupled Hopf oscillators for hexapod locomotion.
    
    This network models six legs with appropriate phase relationships
    for different gaits (e.g., tripod, wave, ripple) and supports
    direction control (forward/backward) and turning behaviors.
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
        
        # Track individual oscillator frequencies and amplitudes
        self.frequencies = np.ones(self.n) * frequency
        self.amplitudes = np.ones(self.n) * amplitude
        
        # Tracking current gait and direction
        self.current_gait = "tripod"
        self.direction_phase = 0.0  # 0 for forward, π for backward
        self.turning = False
        self.turning_direction = None
        self.turning_factor = 0.0
        
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
    
    def set_tripod_gait(self, coupling_strength=1.0, reset_direction=True):
        """
        Set coupling weights and phase biases for tripod gait.
        
        In tripod gait, legs are divided into two groups that move
        in alternation (legs 0, 2, 4 and legs 1, 3, 5).
        
        Args:
            coupling_strength: Strength of coupling between oscillators
            reset_direction: Whether to reset the direction to forward
        """
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
        
        # Apply direction if needed
        if self.direction_phase != 0:
            self._update_phase_relationships()
    
    def set_wave_gait(self, coupling_strength=1.0, reset_direction=True):
        """
        Set coupling weights and phase biases for wave gait.
        
        In wave gait, legs have sequential phase differences of 2π/n.
        This is more stable but slower than tripod gait.
        
        Args:
            coupling_strength: Strength of coupling between oscillators
            reset_direction: Whether to reset the direction to forward
        """
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
        
        # Apply direction if needed
        if self.direction_phase != 0:
            self._update_phase_relationships()
    
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
    
    def reset(self):
        """Reset the oscillator network."""
        self.state = np.zeros(2 * self.n)
        for i in range(self.n):
            self.state[2*i] = 0.1  # Small initial x value
        self.last_update_time = time.time()
        
        # Reset all amplitudes and frequencies to base values
        for i in range(self.n):
            self.amplitudes[i] = self.amplitude
            self.frequencies[i] = self.base_frequency
        
        # Reset turning state
        self.turning = False
        self.turning_direction = None
        self.turning_factor = 0.0


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
    plt.figure(figsize=(14, 12))
    
    # Tripod gait (forward)
    plt.subplot(3, 1, 1)
    for i in range(cpg.n):
        plt.plot(t, outputs[:, i], label=f'Leg {i}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Tripod Gait CPG Output (Forward)')
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
    plt.subplot(3, 1, 2)
    for i in range(cpg.n):
        plt.plot(t, wave_outputs[:, i], label=f'Leg {i}')
        plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Wave Gait CPG Output')
    plt.legend()
    plt.grid(True)
    
    # Reset and demonstrate turning
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.turn_right(turning_factor=0.5)
    
    # Simulate turning
    turning_outputs = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        turning_outputs[i] = cpg.update(dt)
    
    # Turning visualization
    plt.subplot(3, 1, 3)
    for i in range(cpg.n):
        if i % 2 == 0:  # Right legs
            plt.plot(t, turning_outputs[:, i], label=f'Right Leg {i}', linestyle='--')
        else:  # Left legs
            plt.plot(t, turning_outputs[:, i], label=f'Left Leg {i}')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Tripod Gait with Right Turn (0.5 turning factor)')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # Example of more complex maneuver sequence
    if False:  # Set to True to run this example
        print("Demonstrating a sequence of maneuvers...")
        cpg.reset()
        
        # Total simulation time and timestep
        total_time = 15.0  # 15 seconds
        dt = 0.01  # 10ms timestep
        steps = int(total_time / dt)
        
        # Arrays to store the oscillator outputs
        maneuver_outputs = np.zeros((steps, cpg.n))
        maneuver_times = np.linspace(0, total_time, steps)
        
        # Start with forward tripod gait
        cpg.set_tripod_gait()
        
        for i in range(steps):
            # At t=3s, start turning right
            if i == int(3/dt):
                print("Starting right turn...")
                cpg.turn_right(turning_factor=0.4)
            
            # At t=6s, stop turning and go straight
            elif i == int(6/dt):
                print("Stopping turn, going straight...")
                cpg.stop_turning()
            
            # At t=8s, switch to wave gait
            elif i == int(8/dt):
                print("Switching to wave gait...")
                cpg.set_wave_gait()
            
            # At t=10s, start going backward
            elif i == int(10/dt):
                print("Going backward...")
                cpg.set_backward()
            
            # At t=12s, turn left while going backward
            elif i == int(12/dt):
                print("Turning left while going backward...")
                cpg.turn_left(turning_factor=0.3)
            
            # Update the network and store the output
            maneuver_outputs[i] = cpg.update(dt)
        
        # Plot the complex maneuver sequence
        plt.figure(figsize=(14, 8))
        for i in range(cpg.n):
            plt.plot(maneuver_times, maneuver_outputs[:, i], label=f'Leg {i}')
        
        # Add vertical lines to mark events
        plt.axvline(x=3, color='k', linestyle='--', alpha=0.5, label='Start Right Turn')
        plt.axvline(x=6, color='k', linestyle='-.', alpha=0.5, label='Stop Turn')
        plt.axvline(x=8, color='r', linestyle='--', alpha=0.5, label='Wave Gait')
        plt.axvline(x=10, color='r', linestyle='-.', alpha=0.5, label='Backward')
        plt.axvline(x=12, color='g', linestyle='--', alpha=0.5, label='Left Turn')
        
        plt.xlabel('Time (s)')
        plt.ylabel('Amplitude')
        plt.title('Complex Maneuver Sequence')
        plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))
        plt.grid(True)
        plt.tight_layout()
        plt.show()