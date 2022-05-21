# lumigo_opentelemetry :stars:

![CircleCI](https://circleci.com/gh/lumigo-io/lumigo_opentelemetry/tree/master.svg?style=svg&circle-token=d98d1b95f34b49be2caa58c49d8a70d6a7587b88)
![Version](https://badge.fury.io/py/lumigo_opentelemetry.svg)
![codecov](https://codecov.io/gh/lumigo-io/lumigo_opentelemetry/branch/master/graph/badge.svg?token=d8CvqyKTnq)

This is [`lumigo_opentelemetry`](https://pypi.org/project/lumigo_opentelemetry/) package, Lumigo's OpenTelemetry distribution for Python.

Supported Python Runtimes: 3.6, 3.7, 3.8, 3.9, 3.10

# Usage

The `lumigo_opentelemetry` package must be a dependency of your application.
In most cases, you will add `lumigo_opentelemetry` as a line in `requirements.txt`:

```txt
lumigo_opentelemetry
```

Then, import `lumigo_opentelemetry` at the beginning of your main file:

```python
import lumigo_opentelemetry
```

Finally, set the `LUMIGO_TRACER_TOKEN` environment variable on your application with the token you will find in Lumigo under `Settings -> Tracing -> Manual tracing`.

# Configuration

The `lumigo_opentelemetry` offers several different configuration options. Pass modify the environment variables:

* `LUMIGO_TRACER_TOKEN`: Required configuration to send data to Lumigo; you will find the right value in Lumigo under `Settings -> Tracing -> Manual tracing`.
* `LUMIGO_DEBUG=TRUE`: Enables debug logging
* `LUMIGO_DEBUG_SPANDUMP`: path to a local file where to write a local copy of the spans that will be sent to Lumigo; this option handy for local testing but **should not be used in production** unless you are instructed to do so by Lumigo support.
* `LUMIGO_SECRET_MASKING_REGEX=["regex1", "regex2"]`: Prevents Lumigo from sending keys that match the supplied regular expressions. All regular expressions are case-insensitive. By default, Lumigo applies the following regular expressions: `[".*pass.*", ".*key.*", ".*secret.*", ".*credential.*", ".*passphrase.*"]`. 

# Contributing

Contributions to this project are welcome from all! Below are a couple pointers on how to prepare your machine, as well as some information on testing.

## Preparing your machine
Getting your machine ready to develop against the package is a straightforward process:

1. Clone this repository, and open a CLI in the cloned directory
1. Create a virtual environment for the project `virtualenv venv -p python3`
1. Activate the virtualenv: `. venv/bin/activate`
1. Install dependencies: `pip install -r requirements.txt`
1. Navigate to the source directory: `cd src` and 
1. Run the setup script: `python setup.py develop`.
1. Run `pre-commit install` in your repository to install pre-commit hooks

**Note**: If you are using pycharm, ensure that you set it to use the virtualenv virtual environment manager. This is available in the menu under PyCharm -> Preferences -> Project -> Interpreter


## Running the test suite
We've provided an easy way to run the unit test suite:
* Run `./scripts/checks.sh` in the root folder.
