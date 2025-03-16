import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import time
import serial

class CoupledOscillatorNetwork:
    """
    A network of coupled Hopf oscillators for hexapod locomotion.
    
    This network models six legs with appropriate phase relationships
    for different gaits (e.g., tripod, wave, ripple) and can control
    direction and turning behaviors.
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
        
        # Dictionary to map leg indices to leg names
        self.leg_names = {
            0: "frontright",
            1: "frontleft",
            2: "midright",
            3: "midleft",
            4: "backright",
            5: "backleft"
        }
        
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
        """
        Set coupling weights and phase biases for tripod gait.
        
        In tripod gait, legs are divided into two groups that move
        in alternation (legs 0, 2, 4 and legs 1, 3, 5).
        
        Args:
            coupling_strength: Strength of coupling between oscillators
            reset_direction: Whether to reset direction to forward
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
        
        # Update phase relationships if direction is backward
        if self.direction_phase != 0:
            self._update_phase_relationships()
    
    def set_wave_gait(self, coupling_strength=1.0, reset_direction=True):
        """
        Set coupling weights and phase biases for wave gait.
        
        In wave gait, legs have sequential phase differences of 2π/n.
        This is more stable but slower than tripod gait.
        
        Args:
            coupling_strength: Strength of coupling between oscillators
            reset_direction: Whether to reset direction to forward
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
        
        # Update phase relationships if direction is backward
        if self.direction_phase != 0:
            self._update_phase_relationships()
    
    def get_active_legs(self, threshold=0.5):
        """
        Determine which legs are currently in the active phase of the oscillation.
        
        Args:
            threshold: Value above which an oscillator is considered active
            
        Returns:
            List of leg names that are currently active
        """
        active_legs = []
        for i in range(self.n):
            if self.state[2*i] > threshold:
                active_legs.append(self.leg_names[i])
        
        return active_legs
    
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

class HexapodController:
    """
    Controller class for hexapod robot that translates CPG outputs to leg commands
    and handles serial communication.
    """
    def __init__(self, serial_port=None, baud_rate=9600):
        """
        Initialize the hexapod controller.
        
        Args:
            serial_port: Serial port for communication with the robot
            baud_rate: Baud rate for serial communication
        """
        self.cpg = CoupledOscillatorNetwork(n_oscillators=6, frequency=1.0)
        self.last_active_legs = []
        
        # Dictionary to map leg indices to leg names
        self.leg_names = {
            0: "frontright",
            1: "frontleft",
            2: "midright",
            3: "midleft",
            4: "backright",
            5: "backleft"
        }
        
        # Setup serial communication if port is provided
        self.serial_enabled = serial_port is not None
        if self.serial_enabled:
            self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
            self.ser.flush()
    
    def update(self, dt=None):
        """
        Update the controller state and send commands to robot.
        
        Args:
            dt: Time step for CPG update
            
        Returns:
            List of active leg names
        """
        # Update CPG
        outputs = self.cpg.update(dt)
        
        # Get list of active legs (where output > 0.5)
        active_legs = []
        for i in range(self.cpg.n):
            if outputs[i] > 0.5:
                active_legs.append(self.leg_names[i])
        
        # Check if the active legs have changed
        if active_legs != self.last_active_legs:
            # Send commands for newly active legs
            for leg in active_legs:
                if leg not in self.last_active_legs:
                    self._send_command(leg)
                    
            # If all legs are inactive, send the "off" command
            if not active_legs:
                self._send_command("off")
            
            # Update last active legs
            self.last_active_legs = active_legs.copy()
        
        return active_legs
    
    def _send_command(self, command):
        """
        Send a command to the robot.
        
        Args:
            command: String command to send
        """
        print(f"Command: {command}")
        
        if self.serial_enabled:
            self.ser.write(f"{command}\n".encode())
    
    def set_gait(self, gait_type):
        """
        Set the gait type for the hexapod.
        
        Args:
            gait_type: String indicating gait type ("tripod" or "wave")
        """
        if gait_type.lower() == "tripod":
            self.cpg.set_tripod_gait()
            print("Set tripod gait")
        elif gait_type.lower() == "wave":
            self.cpg.set_wave_gait()
            print("Set wave gait")
        else:
            print(f"Unknown gait type: {gait_type}")
    
    def set_direction(self, direction):
        """
        Set the movement direction for the hexapod.
        
        Args:
            direction: String indicating direction ("forward" or "backward")
        """
        if direction.lower() == "forward":
            self.cpg.set_forward()
            print("Set direction: forward")
        elif direction.lower() == "backward":
            self.cpg.set_backward()
            print("Set direction: backward")
        else:
            print(f"Unknown direction: {direction}")
    
    def turn(self, direction, factor=0.3):
        """
        Make the hexapod turn.
        
        Args:
            direction: String indicating turn direction ("left" or "right")
            factor: Turn sharpness factor (0.0 to 1.0)
        """
        if direction.lower() == "left":
            self.cpg.turn_left(factor)
            print(f"Turning left (factor: {factor})")
        elif direction.lower() == "right":
            self.cpg.turn_right(factor)
            print(f"Turning right (factor: {factor})")
        else:
            print(f"Unknown turn direction: {direction}")
    
    def stop_turning(self):
        """Stop turning."""
        self.cpg.stop_turning()
        print("Stopped turning")
    
    def reset(self):
        """Reset the controller."""
        self.cpg.reset()
        self.last_active_legs = []
        self._send_command("off")
        print("Controller reset")


def visualize_gait_patterns(simulation_time=5.0, sample_rate=100):
    """
    Visualize different gait patterns for hexapod locomotion.
    
    Args:
        simulation_time: Duration of simulation in seconds
        sample_rate: Number of samples per second
    """
    # Create a CPG network with 6 oscillators at 1Hz
    cpg = CoupledOscillatorNetwork(n_oscillators=6, frequency=1.0)
    
    # Time points for simulation
    t = np.linspace(0, simulation_time, int(simulation_time * sample_rate))
    dt = t[1] - t[0]
    
    # Dictionary to store results for different gaits and movements
    results = {}
    
    # 1. Tripod gait forward
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.set_forward()
    tripod_forward = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        tripod_forward[i] = cpg.update(dt)
    results["Tripod Forward"] = tripod_forward
    
    # 2. Tripod gait backward
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.set_backward()
    tripod_backward = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        tripod_backward[i] = cpg.update(dt)
    results["Tripod Backward"] = tripod_backward
    
    # 3. Wave gait forward
    cpg.reset()
    cpg.set_wave_gait()
    cpg.set_forward()
    wave_forward = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        wave_forward[i] = cpg.update(dt)
    results["Wave Forward"] = wave_forward
    
    # 4. Wave gait backward
    cpg.reset()
    cpg.set_wave_gait()
    cpg.set_backward()
    wave_backward = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        wave_backward[i] = cpg.update(dt)
    results["Wave Backward"] = wave_backward
    
    # 5. Turning left
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.turn_left(0.5)
    turn_left = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        turn_left[i] = cpg.update(dt)
    results["Turn Left"] = turn_left
    
    # 6. Turning right
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.turn_right(0.5)
    turn_right = np.zeros((len(t), cpg.n))
    for i in range(len(t)):
        turn_right[i] = cpg.update(dt)
    results["Turn Right"] = turn_right
    
    # Plot all results
    fig, axes = plt.subplots(3, 2, figsize=(18, 12))
    axes = axes.flatten()
    leg_names = ["Front Right", "Front Left", "Mid Right", "Mid Left", "Back Right", "Back Left"]
    
    for i, (title, data) in enumerate(results.items()):
        ax = axes[i]
        for j in range(cpg.n):
            ax.plot(t, data[:, j], label=leg_names[j])
        
        # For turning movements, add amplitude/frequency difference explanation
        if "Turn" in title:
            asymmetry = []
            for j in range(cpg.n):
                if "Left" in title:
                    # For left turn, right legs have higher amplitudes
                    is_important = j % 2 == 0
                else:
                    # For right turn, left legs have higher amplitudes
                    is_important = j % 2 == 1
                    
                if is_important:
                    asymmetry.append(f"{leg_names[j]} (↑)")
                
            asymmetry_str = ", ".join(asymmetry)
            ax.text(0.5, -0.15, f"Higher amplitude & frequency: {asymmetry_str}",
                    horizontalalignment='center', transform=ax.transAxes)
            
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Output')
        ax.set_title(title)
        ax.legend()
        ax.grid(True)
    
    plt.tight_layout()
    plt.show()


def simulate_walking_sequence(duration=10.0):
    """
    Simulate a walking sequence and print leg activation patterns.
    
    Args:
        duration: Duration of simulation in seconds
    """
    controller = HexapodController()
    
    # Start with tripod gait
    controller.set_gait("tripod")
    controller.set_direction("forward")
    
    # Run simulation
    start_time = time.time()
    elapsed = 0
    
    print("Simulating hexapod walking sequence:")
    print("-----------------------------------")
    
    # Track the active legs and when they change
    while elapsed < duration:
        # Get current time
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Change movement pattern based on time
        if elapsed > 8.0:
            # Stop and reset at the end
            controller.reset()
            break
        elif elapsed > 6.0:
            # Turn right in last phase
            if controller.cpg.turning_direction != "right":
                controller.turn("right", 0.5)
        elif elapsed > 4.0:
            # Turn left in middle phase
            if controller.cpg.turning_direction != "left":
                controller.turn("left", 0.5)
        elif elapsed > 2.0:
            # Switch to wave gait after 2 seconds
            if controller.cpg.current_gait != "wave":
                controller.set_gait("wave")
        
        # Update controller state
        active_legs = controller.update(0.05)  # 50ms update interval
        
        # Add a small delay to not overload the console output
        time.sleep(0.05)
    
    print("-----------------------------------")
    print("Simulation complete")


def leg_command_translator(outputs, threshold=0.5):
    """
    Translate oscillator outputs to leg command strings.
    
    Args:
        outputs: Array of oscillator outputs for each leg
        threshold: Threshold above which a leg is considered active
        
    Returns:
        String command representing active legs
    """
    leg_names = {
        0: "frontright",
        1: "frontleft",
        2: "midright",
        3: "midleft",
        4: "backright",
        5: "backleft"
    }
    
    active_legs = []
    for i, output in enumerate(outputs):
        if output > threshold:
            active_legs.append(leg_names[i])
    
    if not active_legs:
        return "off"
    elif len(active_legs) == len(leg_names):
        return "all"
    else:
        return ",".join(active_legs)


# Main demonstration code
if __name__ == "__main__":
    print("Hexapod Locomotion Controller")
    print("============================")
    print("\n1. Visualizing gait patterns...")
    visualize_gait_patterns()
    
    print("\n2. Simulating walking sequence with changing gaits and turning...")
    simulate_walking_sequence()
    
    print("\n3. Demonstrating leg command generation for different gaits...")
    
    # Create a CPG network for demonstration
    cpg = CoupledOscillatorNetwork(n_oscillators=6, frequency=1.0)
    
    # Simulate for 2 seconds with 10 points per second
    t = np.linspace(0, 2, 20)
    dt = t[1] - t[0]
    
    # Demonstrate tripod gait commands
    print("\nTripod gait leg commands:")
    cpg.reset()
    cpg.set_tripod_gait()
    for i in range(len(t)):
        outputs = cpg.update(dt)
        command = leg_command_translator(outputs)
        print(f"Time {t[i]:.2f}s: {command}")
    
    # Demonstrate wave gait commands
    print("\nWave gait leg commands:")
    cpg.reset()
    cpg.set_wave_gait()
    for i in range(len(t)):
        outputs = cpg.update(dt)
        command = leg_command_translator(outputs)
        print(f"Time {t[i]:.2f}s: {command}")
    
    # Demonstrate turning commands
    print("\nTurning right leg commands (note the asymmetric amplitude and frequency):")
    cpg.reset()
    cpg.set_tripod_gait()
    cpg.turn_right(0.5)
    for i in range(len(t)):
        outputs = cpg.update(dt)
        command = leg_command_translator(outputs)
        print(f"Time {t[i]:.2f}s: {command}")
    
    print("\nHexapod controller demonstration complete.")
