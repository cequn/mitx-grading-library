"""
specify_domain.py

Defines class SpecifyDomain, an author-facing decorator for specifying the domain
of a function. Currently only supports specifying the shape of inputs.
"""
from numbers import Number
from voluptuous import Schema, Invalid, All, Any, Required, Coerce
from mitxgraders.helpers.validatorfuncs import Positive
from mitxgraders.baseclasses import StudentFacingError, ObjectWithSchema
from mitxgraders.helpers.math_array import MathArray, is_scalar_matharray

def low_ordinal(n):
    """
    For n<10, returns correct ordinal 1st, 2nd, ... ; otherwise, returns nth.

    >>> [low_ordinal(n) for n in range(5)]
    ['0th', '1st', '2nd', '3rd', '4th']
    >>> low_ordinal(21)
    '21th'
    """
    first_three = {1: '1st', 2: '2nd', 3: '3rd'}
    return first_three.get(n, '{0}th'.format(n))

def get_description(obj):
    """
    Gets a student-facing description of obj.

    Numbers return scalar:
    >>> get_description(5)
    'scalar'

    MathArrays return their own description:
    >>> get_description(MathArray([1, 2, 3]))
    'vector of length 3'

    Other objects return their class name:
    >>> get_description("puppy")
    'str'
    """
    if isinstance(obj, Number):
        return 'scalar'
    elif isinstance(obj, MathArray):
        return obj.description
    else:
        return obj.__class__.__name__

class DomainError(StudentFacingError):
    """
    Raised when a function has domain error.
    """

def number_validator(obj):
    """
    Voluptuous validator to test that obj is number.

    >>> number_validator(5) == 5
    True
    >>> number_validator(MathArray(5)) == 5
    True

    Provides a useful error message:
    >>> number_validator(MathArray([1, 2, 3]))
    Traceback (most recent call last):
    Invalid: received a vector of length 3, expected a scalar
    >>> number_validator([1, 2, 3])
    Traceback (most recent call last):
    Invalid: received a list, expected a scalar

    """
    if isinstance(obj, Number):
        return obj
    elif is_scalar_matharray(obj):
        return obj.item()

    raise Invalid("received a {0}, expected a scalar".format(get_description(obj)))


def make_shape_validator(shape):
    """
    Returns a voluptuous validator that tests whether argument is a MathArray
    with specified shape.

    Arguments:
    =========
        shape (tuple): A numpy shape tuple

    Usage:
    ======
    >>> validate_vec4 = make_shape_validator((4,))
    >>> vec4 = MathArray([1, 2, 3, 4])
    >>> validate_vec4(vec4)
    MathArray([1, 2, 3, 4])

    Provides useful error messages if obj is a number or MathArray:
    >>> validate_vec4(MathArray([[1, 2, 3], [4, 5, 6]]))
    Traceback (most recent call last):
    Invalid: received a matrix of shape (rows: 2, cols: 3), expected a vector of length 4
    >>> validate_vec4('cat')
    Traceback (most recent call last):
    Invalid: received a str, expected a vector of length 4
    """
    def shape_validator(obj):
        if isinstance(obj, MathArray) and obj.shape == shape:
            return obj
        raise Invalid("received a {received}, expected a {expected}"
            .format(received=get_description(obj), expected=MathArray.get_description(shape)))

    return shape_validator

def has_shape(shape):
    if shape == (1,):
        return number_validator
    return make_shape_validator(shape)

# how authors specify domain shape
SCHEMA_SHAPE = Schema(Any(
    All(Positive(int), lambda x: tuple([x])),
    All([Positive(int)], Coerce(tuple)),
    msg='Expected shape specification to be a positive integer or list of positive integers'
))

class SpecifyDomain(ObjectWithSchema):
    """
    An author-facing, configurable decorator that validates the inputs
    of the decorated function.

    For now, the only validation available is shape-validation.

    Configuration
    =============
    - input_shapes (list): A list of shapes for the function inputs, where:
        1: means input is scalar
        k, positive integer: means input is a k-component vector
        [k1, k2, ...], list of positive integers: means input is an array of shape [k1, k2, ...]
    - display_name (?str): Function name to be used in error messages
      defaults to None, meaning that the function's __name__ attribute is used.

    Basic Usage:
    ============

    Validate that both inputs to a cross product function are 3-component MathArrays:
    >>> import numpy as np          # just to get the cross product
    >>> @SpecifyDomain(input_shapes=[3, 3])
    ... def cross(u, v):
    ...     return np.cross(u, v)

    If inputs are valid, the function is calculated:
    >>> a = MathArray([2, -1, 3])
    >>> b = MathArray([-1, 4, 1])
    >>> np.array_equal(
    ...     cross(a, b),
    ...     np.cross(a, b)
    ... )
    True

    If inputs are bad, student-facing DomainErrors are thrown:
    >>> a = MathArray([2, -1, 3])
    >>> b = MathArray([-1, 4])
    >>> cross(a, b)                                 # doctest: +ELLIPSIS
    Traceback (most recent call last):
    DomainError: There was an error evaluating function cross(...)
    ...1st input is ok: received a vector of length 3 as expected
    ...2nd input has an error: received a vector of length 2, expected a vector of length 3
    >>> cross(a)
    Traceback (most recent call last):
    DomainError: There was an error evaluating function cross(...): expected 2 inputs, but received 1.
    """

    schema_config = Schema({
        Required('input_shapes'): [SCHEMA_SHAPE],
        Required('display_name', default=None): str
    })

    def __init__(self, config=None, **kwargs):
        super(SpecifyDomain, self).__init__(config, **kwargs)

        display_name = self.config['display_name']
        shapes = self.config['input_shapes']
        self.decorate = self.make_decorator(*shapes, display_name=display_name)

    def __call__(self, func):
        return self.decorate(func)

    @staticmethod
    def make_decorator(*shapes, **kwargs):
        """
        Constructs the decorator that validates inputs.

        This method is NOT author-facing; its inputs undero no validation.

        Used internally in mitxgraders library.
        """

        display_name = kwargs.get('display_name', None)
        schemas = [Schema(has_shape(shape)) for shape in shapes]

        # can't use @wraps, func might be a numpy ufunc
        def decorator(func):
            func_name = display_name if display_name else func.__name__
            def _func(*args):
                if len(shapes) != len(args):
                    msg = ("There was an error evaluating function "
                           "{func_name}(...): expected {expected} inputs, but "
                           "received {received}."
                           .format(func_name=func_name, expected=len(shapes), received=len(args))
                          )
                    raise DomainError(msg)

                errors = []
                for schema, arg in zip(schemas, args):
                    try:
                        schema(arg)
                        errors.append(None)
                    except Invalid as error:
                        errors.append(error)

                if all([error is None for error in errors]):
                    return func(*args)

                lines = ['There was an error evaluating function {0}(...)'.format(func_name)]
                for index, (shape, error) in enumerate(zip(shapes, errors)):
                    ordinal = low_ordinal(index + 1)
                    if error:
                        lines.append('{0} input has an error: '.format(ordinal) + error.error_message)
                    else:
                        expected = 'scalar' if shape == (1,) else MathArray.get_description(shape)
                        lines.append('{0} input is ok: received a {1} as expected'
                            .format(ordinal, expected))

                message = "\n\t".join(lines)
                raise DomainError(message)

            _func.__name__ = func.__name__
            _func.validated = True
            return _func


        return decorator

specify_domain = SpecifyDomain
