"""Selected unchanged historical transition functions."""
import cmath

def drift(z):
    return (1.06 + 0.015 * abs(z)**2) * z + complex(0.12, -0.08)


def transition(z, phi, omega, previous_action, action, coupling=0.3):
    return (drift(z) + cmath.exp(1j * phi) * action,
            phi + omega + coupling * previous_action.real * previous_action.imag)
