**Table of Contents**

- [MITx Graders](#mitx-graders)
- [Installation](#installation)
- [Usage in edX](#usage-in-edx)
- [Grader Documentation](#grader-documentation)

# MITx Graders

A library of graders for edX Custom Response problems.

Version 0.2.0

Copyright 2017 Jolyon Bloomfield and Chris Chudzicki

# Installation

To install:

This is useful for testing configurations in python, rather than in edX. However, this is not necessary.

**Requirements:** An installation of Python 2.7 (since this is what edX uses).

0. (Optional) Create and activate a new python virtual environment.
1. Clone this repository and `cd` into it.
2. Run `pip install -r requirements.txt` to install the requirements specified in `requirements.txt`.
3. Run `pytest` to check that tests are passing.

To use in edX:

1. Download [python_lib.zip](python_lib.zip) and place it in your static folder (XML workflow) or upload it as a file asset (Studio workflow).

# Usage in edX

In edX, you want to use a Custom Response problem. We provide examples of the XML required to use the grading library in edX.

A custom response problem is defined using the customresponse tag. It needs to be supplied a check function (cfn), which must be a grader that you have defined in the problem.

The basic pattern is the following.

```xml
<script type="text/python" system_path="python_lib">
import graders
mygrader = GraderType(
    [configuration]
)
</script>

<customresponse cfn="mygrader">
    <textline/>
</customresponse>
```

The configuration depends on the type of grader that you're using. Note that all answers must be passed through the configuration; the `expect` keyword is not used to pass the answer, but is used when a student clicks "Show Answer".

Here is an example where we use a StringGrader with answer `cat`.

```xml
<script type="text/python" system_path="python_lib">
import graders
mygrader = StringGrader(
    answers='cat'
)
</script>

<customresponse cfn="mygrader">
    <textline/>
</customresponse>
```

Here is another example where we use a ListGrader to grade two numbers in an unordered fashion.

```xml
<script type="text/python" system_path="python_lib">
import graders
mygrader = ListGrader(
    answers=['1', '2']
    subgrader=FormulaGrader()
)
</script>

<customresponse cfn="mygrader">
    <textline/>
    <textline/>
</customresponse>
```

TODO: Documentation on how the `expect` keyword works.

# Grader Documentation

[Extensive documentation](docs/README.md) has been compiled for the configuration of the different graders in the library.
