"""
sampling.py

Contains classes for sampling numerical values
* RealInterval
* IntegerRange
* DiscreteSet
* ComplexRectangle
* ComplexSector
and for specifying functions
* SpecificFunctions
* RandomFunction
"""
from __future__ import division
from numbers import Number
import abc
import random
import numpy as np
from graders.baseclasses import ObjectWithSchema, ConfigError
from graders.voluptuous import Schema, Required
from graders.helpers.validatorfuncs import (Positive, NumberRange, ListOfType,
                                            TupleOfType, is_callable)

# Set the objects to be imported from this grader
__all__ = [
    "RealInterval",
    "IntegerRange",
    "DiscreteSet",
    "ComplexRectangle",
    "ComplexSector",
    "SpecificFunctions",
    "RandomFunction"
]

class AbstractSamplingSet(ObjectWithSchema):  # pylint: disable=abstract-method
    """Represents a set from which random samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def gen_sample(self):
        """Generate a sample from this sampling set"""
        pass


class VariableSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random variable samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class FunctionSamplingSet(AbstractSamplingSet):  # pylint: disable=abstract-method
    """Represents a set from which random function samples are taken."""

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta


class RealInterval(VariableSamplingSet):
    """
    Represents an interval of real numbers from which to sample.

    Usage
    =====
    Generate 5 random floats betweens -2 and 4
    >>> ri = RealInterval(start=-2, stop=4)
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.44247 -0.67699 -1.36759 -0.11255  1.39864]

    You can also initialize with an interval:
    >>> ri = RealInterval([-2,4])
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.9973   2.95767  0.069    0.23813 -1.49541]

    The default is start=1, stop=5:
    >>> ri = RealInterval()
    >>> [ri.gen_sample() for j in range(5)] # doctest: +SKIP
    [ 2.61484  1.38107  2.61687  1.00507  1.87933]
    """
    schema_config = NumberRange()

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(RealInterval, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random real number in the range [start, stop]"""
        start, stop = self.config['start'], self.config['stop']
        return start + (stop - start) * np.random.random_sample()


class IntegerRange(VariableSamplingSet):
    """
    Represents an interval of integers from which to sample.

    Specify start and stop or [start, stop] to initialize.

    Both start and stop are included in the interval.

    Usage
    =====
    Generate 5 random floats betweens -2 and 4
    >>> integer = IntegerRange(start=-2, stop=4)
    >>> integer.gen_sample() in list(range(-2,5))
    True

    You can also initialize with an interval:
    >>> integer = IntegerRange([-2,4])
    >>> integer.gen_sample() in list(range(-2,5))
    True

    The default is start=1, stop=5:
    >>> integer = IntegerRange()
    >>> integer.gen_sample() in list(range(1,6))
    True
    """
    schema_config = NumberRange(int)

    def __init__(self, config=None, **kwargs):
        """
        Validate the specified configuration.
        First apply the voluptuous validation.
        Then ensure that the start and stop are the right way around.
        """
        super(IntegerRange, self).__init__(config, **kwargs)
        if self.config['start'] > self.config['stop']:
            self.config['start'], self.config['stop'] = self.config['stop'], self.config['start']

    def gen_sample(self):
        """Returns a random integer in range(start, stop)"""
        return np.random.randint(low=self.config['start'], high=self.config['stop'] + 1)


class ComplexRectangle(VariableSamplingSet):
    """
    Represents a rectangle in the complex plane from which to sample.

    Usage
    =====
    >>> rect = ComplexRectangle(re=[1,4], im=[-5,0])
    >>> rect.gen_sample() # doctest: +SKIP
    (1.90313791936 - 2.94195943775j)
    """
    schema_config = Schema({
        Required('re', default=[1, 3]): NumberRange(),
        Required('im', default=[1, 3]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the real and imaginary
        parts as RealInterval objects
        """
        super(ComplexRectangle, self).__init__(config, **kwargs)
        self.re = RealInterval(self.config['re'])
        self.im = RealInterval(self.config['im'])

    def gen_sample(self):
        """Generates a random sample in the defined rectangle in the complex plane"""
        return self.re.gen_sample() + self.im.gen_sample()*1j


class ComplexSector(VariableSamplingSet):
    """
    Represents an annular sector in the complex plane from which to sample,
    based on a given range of modulus and argument.

    Usage
    =====
    >>> sect = ComplexSector(modulus=[0,1], argument=[-np.pi,np.pi])
    >>> sect.gen_sample() # doctest: +SKIP
    (0.022537684419662009+0.093135340148676249j)
    """
    schema_config = Schema({
        Required('modulus', default=[1, 3]): NumberRange(),
        Required('argument', default=[0, np.pi/2]): NumberRange()
    })

    def __init__(self, config=None, **kwargs):
        """
        Configure the class as normal, then set up the modulus and argument
        parts as RealInterval objects
        """
        super(ComplexSector, self).__init__(config, **kwargs)
        self.modulus = RealInterval(self.config['modulus'])
        self.argument = RealInterval(self.config['argument'])

    def gen_sample(self):
        """Generates a random sample in the defined annular sector in the complex plane"""
        return self.modulus.gen_sample() * np.exp(1j * self.argument.gen_sample())


class RandomFunction(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Generates a random well-behaved function on demand.

    Currently implemented as a sum of trigonometric functions with
    random amplitude, frequency and phase. You can control the center and amplitude of
    the resulting oscillations by specifying center and amplitude.

    Usage
    =====
    Generate a random continous function:
    >>> funcs = RandomFunction()
    >>> f = funcs.gen_sample()
    >>> [f(1.2), f(1.2), f(1.3), f(4)] # doctest: +SKIP
    [-1.89324 -1.89324 -2.10722  0.85814]

    By default, the generated functions are R-->R. You can specify the
    input and output dimensions:
    >>> funcs = RandomFunction(input_dim=3, output_dim=2)
    >>> f = funcs.gen_sample()
    >>> f(2.3, -1, 4.2) # doctest: +SKIP
    [-1.74656 -0.96909]
    >>> f(2.3, -1.1, 4.2) # doctest: +SKIP
    [-1.88769 -1.32087]
    """

    schema_config = Schema({
        Required('input_dim', default=1): Positive(int),
        Required('output_dim', default=1): Positive(int),
        Required('num_terms', default=3): Positive(int),
        Required('center', default=0): Number,
        Required('amplitude', default=10): Positive(Number)
    })

    def gen_sample(self):
        """
        Returns a randomly chosen 'nice' function.

        The output is a vector with output_dim dimensions:
        Y^i = sum_{jk} A^i_{jk} sin(B^i_{jk} X_k + C^i_{jk})

        i ranges from 1 to output_dim
        j ranges from 1 to num_terms
        k ranges from 1 to input_dim
        """
        # Generate arrays of random values for A, B and C
        output_dim = self.config['output_dim']
        input_dim = self.config['input_dim']
        num_terms = self.config['num_terms']
        # Amplitudes A range from 0.5 to 1
        A = np.random.rand(output_dim, num_terms, input_dim) / 2 + 0.5
        # Angular frequencies B range from -pi to pi
        B = 2 * np.pi * (np.random.rand(output_dim, num_terms, input_dim) - 0.5)
        # Phases C range from 0 to 2*pi
        C = 2 * np.pi * np.random.rand(output_dim, num_terms, input_dim)

        def f(*args):
            """Function that generates the random values"""
            # Check that the dimensions are correct
            if len(args) != input_dim:
                msg = "Expected {} arguments, but received {}".format(input_dim, len(args))
                raise ConfigError(msg)

            # Turn the inputs into an array
            xvec = np.array(args)
            # Repeat it into the shape of A, B and C
            xarray = np.tile(xvec, (output_dim, num_terms, 1))
            # Compute the output matrix
            output = A * np.sin(B * xarray + C)
            # Sum over the j and k terms
            # We have an old version of numpy going here, so we can't use
            # fullsum = np.sum(output, axis=(1, 2))
            fullsum = np.sum(np.sum(output, axis=2), axis=1)

            # Scale and translate to fit within center and amplitude
            fullsum = fullsum * self.config["amplitude"] / self.config["num_terms"]
            fullsum += self.config["center"]

            # Return the result
            return fullsum if output_dim > 1 else fullsum[0]

        return f


class DiscreteSet(VariableSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a discrete set of values from which to sample.

    Can be initialized with a single value or a non-empty tuple of values.

    Note that we use a tuple instead of a list so that [0,1] isn't confused with (0,1).
    We would use a set, but unfortunately voluptuous doesn't work with sets.

    Usage
    =====
    >>> values = DiscreteSet(3.142)
    >>> values.gen_sample() == 3.142
    True
    >>> values = DiscreteSet((1,2,3,4))
    >>> values.gen_sample() in (1,2,3,4)
    True
    """

    # Take in an individual or tuple of numbers
    schema_config = Schema(TupleOfType(Number))

    def gen_sample(self):
        """Return a random entry from the given set"""
        return random.choice(self.config)


class SpecificFunctions(FunctionSamplingSet):  # pylint: disable=too-few-public-methods
    """
    Represents a set of user-defined functions for use in a grader, one of which will
    be randomly selected. A single function can be provided here, but this is intended
    for lists of functions to be randomly sampled from.

    Usage
    =====

    >>> functions = SpecificFunctions([np.sin, np.cos, np.tan])
    >>> functions.gen_sample() in [np.sin, np.cos, np.tan]
    True
    >>> step_func = lambda x : 0 if x<0 else 1
    >>> functions = SpecificFunctions(step_func)
    >>> functions.gen_sample() == step_func
    True
    """

    # Take in a function or list of callable objects
    schema_config = Schema(ListOfType(object, is_callable))

    def gen_sample(self):
        """Return a random entry from the given list"""
        return random.choice(self.config)