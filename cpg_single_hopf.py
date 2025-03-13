import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import time

class HopfOscillator:
    """
    A simple Hopf oscillator implementation.
    
    This oscillator produces stable limit cycles and is commonly
    used in CPG-based robot locomotion.
    """
    def __init__(self, amplitude=1.0, frequency=1.0, mu=1.0):
        """
        Initialize the Hopf oscillator.
        
        Args:
            amplitude: Desired amplitude of oscillation
            frequency: Frequency of oscillation in Hz
            mu: Convergence rate to the limit cycle
        """
        self.amplitude = amplitude
        self.omega = 2 * np.pi * frequency  # Angular frequency
        self.mu = mu
        self.x = 0.1  # Initial state
        self.y = 0.0  # Initial state
        self.last_update_time = time.time()
    
    def equations(self, state, t):
        """
        Differential equations for the Hopf oscillator.
        
        Args:
            state: Current state [x, y]
            t: Time variable (not used, but required by odeint)
        
        Returns:
            Derivatives [dx/dt, dy/dt]
        """
        x, y = state
        
        # Hopf oscillator equations
        dx = self.mu * (self.amplitude - (x**2 + y**2)) * x - self.omega * y
        dy = self.mu * (self.amplitude - (x**2 + y**2)) * y + self.omega * x
        
        return [dx, dy]
    
    def update(self, dt=None):
        """
        Update the oscillator state by integrating over time dt.
        
        Args:
            dt: Time step for integration (if None, uses elapsed time since last update)
        
        Returns:
            Current x value of the oscillator
        """
        if dt is None:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time
        
        # Integrate the system for one time step
        t = np.array([0, dt])
        state = odeint(self.equations, [self.x, self.y], t)
        
        # Update the state
        self.x, self.y = state[-1]
        
        return self.x
    
    def reset(self, x=0.1, y=0.0):
        """Reset the oscillator state."""
        self.x = x
        self.y = y
        self.last_update_time = time.time()

# Demonstration code
if __name__ == "__main__":
    # Create an oscillator with 1Hz frequency
    osc = HopfOscillator(amplitude=1.0, frequency=1.0)
    
    # Simulate for 5 seconds with 100 points per second
    t = np.linspace(0, 5, 500)
    dt = t[1] - t[0]
    
    # Arrays to store the oscillator output
    x_values = []
    y_values = []
    
    # Simulate the oscillator
    for _ in t:
        osc.update(dt)
        x_values.append(osc.x)
        y_values.append(osc.y)
    
    # Plot the results
    plt.figure(figsize=(12, 5))
    
    # Time series plot
    plt.subplot(1, 2, 1)
    plt.plot(t, x_values, 'b-', label='x(t)')
    plt.plot(t, y_values, 'r-', label='y(t)')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Hopf Oscillator Output')
    plt.legend()
    plt.grid(True)
    
    # Phase plot
    plt.subplot(1, 2, 2)
    plt.plot(x_values, y_values, 'g-')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Phase Plot')
    plt.axis('equal')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()