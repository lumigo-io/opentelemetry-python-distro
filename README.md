# Lumigo OpenTelemetry Distro for Python :stars:

[![Tracer Testing](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml/badge.svg)](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml)
![Version](https://badge.fury.io/py/lumigo_opentelemetry.svg)

The Lumigo OpenTelemetry Distribution for Python is a package that provides no-code distributed tracing for containerized applications.

The Lumigo OpenTelemetry Distribution for Python is made of several upstream OpenTelemetry packages, with additional automated quality-assurance and customizations that optimize for no-code injection, meaning that you should need to update exactly zero lines of code in your application in order to make use of the Lumigo OpenTelemetry Distribution.
(See the [No-code instrumentation](#no-code-instrumentation) section for auto-instrumentation instructions)

**Note:** If you are looking for the Lumigo Python tracer for AWS Lambda functions, [`lumigo-tracer`](https://pypi.org/project/lumigo-tracer/) is the package you should use instead.

## Supported Runtimes

* cpython: 3.7.x, 3.8.x, 3.9.x, 3.10.x

## Setup

### Add lumigo_opentelemetry as dependency

The [`lumigo_opentelemetry` package](https://pypi.org/project/lumigo_opentelemetry/) needs to be a dependency of your application.
In most cases, you will add `lumigo_opentelemetry` as a line in `requirements.txt`:

```txt
lumigo_opentelemetry
```

Or, you may use `pip`:

```sh
pip install lumigo_opentelemetry
```

### Environment-based configuration

Configure the `LUMIGO_TRACER_TOKEN` environment variable with the token value generated for you by the Lumigo platform, under `Settings --> Tracing --> Manual tracing`:

```sh
# Replace `<token>` below with the token generated for you by the Lumigo platform
export LUMIGO_TRACER_TOKEN=<token>
```

It is also strongly suggested that you set the `OTEL_SERVICE_NAME` environment variable with, as value, the service name you have chosen for your application:

```sh
# Replace `<service name> with the desired name of the service`
export OTEL_SERVICE_NAME=<service name>
```

### Tracer activation

There are two ways to activate the `lumigo_opentelemetry` package: one based on importing the package in code (manual activation), and the other via the environment (no-code activation).
The [no-code activation](#no-code-activation) approach is the preferred one.

#### No-code activation

**Note:** The instructions in this section are mutually exclusive with those provided in the [Manual instrumentation](#manual-activation) section.

Set the following environment variable:

```sh
export AUTOWRAPT_BOOTSTRAP=lumigo_opentelemetry
```

#### Manual activation

**Note:** The instructions in this section are mutually exclusive with those provided in the [No-code activation](#no-code-activation) section.

Import `lumigo_opentelemetry` at the beginning of your main file:

```python
import lumigo_opentelemetry
```

## Configuration

### OpenTelemetry configurations

The Lumigo OpenTelemetry Distro for Python is made of several upstream OpenTelemetry packages, together with additional logic and, as such, the environment varoables that work with "vanilla" OpenTelemetry work also with the Lumigo OpenTelemetry Distro for Python. Specifically supported are:

* [General configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/sdk-environment-variables.md#general-sdk-configuration)
* [Batch span processor configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/sdk-environment-variables.md#batch-span-processor): The Lumigo OpenTelemetry Distro for Python uses a batch processor for sending data to Lumigo.

### Lumigo-specific configurations

The `lumigo_opentelemetry` package additionally supports the following configuration options as environment variables:

* `LUMIGO_TRACER_TOKEN`: [Required] Required configuration to send data to Lumigo; you will find the right value in Lumigo under `Settings -> Tracing -> Manual tracing`.
* `LUMIGO_DEBUG=TRUE`: Enables debug logging
* `LUMIGO_DEBUG_SPANDUMP`: path to a local file where to write a local copy of the spans that will be sent to Lumigo; this option handy for local testing but **should not be used in production** unless you are instructed to do so by Lumigo support.
* `LUMIGO_SECRET_MASKING_REGEX=["regex1", "regex2"]`: Prevents Lumigo from sending keys that match the supplied regular expressions. All regular expressions are case-insensitive. By default, Lumigo applies the following regular expressions: `[".*pass.*", ".*key.*", ".*secret.*", ".*credential.*", ".*passphrase.*"]`.
* `LUMIGO_SWITCH_OFF=TRUE`: This option disables the Lumigo OpenTelemetry distro entirely; no instrumentation will be injected, no tracing data will be collected. 

## Baseline setup

The Lumigo OpenTelemetry Distro will automatically create the following OpenTelemetry constructs provided to a `TraceProvider`:

* A `Resource` built from the default OpenTelemetry resource with the `sdk...` attributes
* If the `LUMIGO_TRACER_TOKEN` environment variable is set: a [BatchSpanProcessor](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L126), which uses an [`OTLPSpanExporter`](https://github.com/open-telemetry/opentelemetry-python/blob/50093f220f945ae38e769ab539c78c975e582bef/exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/trace_exporter/__init__.py#L55) to push tracing data to Lumigo
* If the `LUMIGO_DEBUG_SPANDUMP` environment variable is set: a [`SimpleSpanProcessor`](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L79), which uses an [`ConsoleSpanExporter`](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L415) to save to file the spans collected. Do not use this in production!

