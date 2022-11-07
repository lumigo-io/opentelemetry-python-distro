# Lumigo OpenTelemetry Distro for Python :stars:

[![Tracer Testing](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml/badge.svg)](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml)
![Version](https://badge.fury.io/py/lumigo_opentelemetry.svg)

The Lumigo OpenTelemetry Distribution for Python is a package that provides no-code distributed tracing for containerized applications.

The Lumigo OpenTelemetry Distribution for Python is made of several upstream OpenTelemetry packages, with additional automated quality-assurance and customizations that optimize for no-code injection, meaning that you should need to update exactly zero lines of code in your application in order to make use of the Lumigo OpenTelemetry Distribution.
(See the [No-code instrumentation](#no-code-instrumentation) section for auto-instrumentation instructions)

**Note:** If you are looking for the Lumigo Python tracer for AWS Lambda functions, [`lumigo-tracer`](https://pypi.org/project/lumigo-tracer/) is the package you should use instead.

## Setup

Adding the Lumigo OpenTelemetry Distro for Python to your application is a three-step process:

1. [Add the Lumigo OpenTelemetry Distro for Python as dependency](#add-lumigo_opentelemetry-as-dependency)
2. [Provide configurations through environment variables](#environment-based-configuration)
3. [Activate the tracer](#tracer-activation), which can also be achieved through environment variables

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

```console
LUMIGO_TRACER_TOKEN=<token>
```

Replace `<token>` below with the token generated for you by the Lumigo platform.

It is also strongly suggested that you set the `OTEL_SERVICE_NAME` environment variable with, as value, the service name you have chosen for your application:

```console
OTEL_SERVICE_NAME=<service name>
```

Replace `<service name> with the desired name of the service`.

**Note:** While you are providing environment variables for configuration, consider also providing the one needed for [no-code tracer activation](#no-code-activation) :-)

### Tracer activation

There are two ways to activate the `lumigo_opentelemetry` package: one based on importing the package in code (manual activation), and the other via the environment (no-code activation).
The [no-code activation](#no-code-activation) approach is the preferred one.

#### No-code activation

**Note:** The instructions in this section are mutually exclusive with those provided in the [Manual instrumentation](#manual-activation) section.

Set the following environment variable:

```console
AUTOWRAPT_BOOTSTRAP=lumigo_opentelemetry
```

#### Manual activation

**Note:** The instructions in this section are mutually exclusive with those provided in the [No-code activation](#no-code-activation) section.

Import `lumigo_opentelemetry` at the beginning of your main file:

```python
import lumigo_opentelemetry
```

## Configuration

### OpenTelemetry configurations

The Lumigo OpenTelemetry Distro for Python is made of several upstream OpenTelemetry packages, together with additional logic and, as such, the environment variables that work with "vanilla" OpenTelemetry work also with the Lumigo OpenTelemetry Distro for Python. Specifically supported are:

* [General configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/sdk-environment-variables.md#general-sdk-configuration)
* [Batch span processor configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/sdk-environment-variables.md#batch-span-processor): The Lumigo OpenTelemetry Distro for Python uses a batch processor for sending data to Lumigo.

### Lumigo-specific configurations

The `lumigo_opentelemetry` package additionally supports the following configuration options as environment variables:

* `LUMIGO_TRACER_TOKEN`: [Required] Required configuration to send data to Lumigo; you will find the right value in Lumigo under `Settings -> Tracing -> Manual tracing`.
* `LUMIGO_DEBUG=TRUE`: Enables debug logging
* `LUMIGO_DEBUG_SPANDUMP`: path to a local file where to write a local copy of the spans that will be sent to Lumigo; this option handy for local testing but **should not be used in production** unless you are instructed to do so by Lumigo support.
* `LUMIGO_SECRET_MASKING_REGEX=["regex1", "regex2"]`: Prevents Lumigo from sending keys that match the supplied regular expressions. All regular expressions are case-insensitive. By default, Lumigo applies the following regular expressions: `[".*pass.*", ".*key.*", ".*secret.*", ".*credential.*", ".*passphrase.*"]`.
* `LUMIGO_SWITCH_OFF=TRUE`: This option disables the Lumigo OpenTelemetry distro entirely; no instrumentation will be injected, no tracing data will be collected. 

## Supported runtimes

* cpython: 3.7.x, 3.8.x, 3.9.x, 3.10.x

## Supported packages

| Instrumentation | Package | Supported Versions |
| --- | --- | --- |
| botocore | [boto3](https://pypi.org/project/boto3) | 1.17.22~1.24.35 |
| fastapi | [fastapi](https://pypi.org/project/fastapi) | 0.56.1~0.86.0 |
| | [uvicorn](https://pypi.org/project/uvicorn) | 0.11.3~0.19.0 |
| flask | [flask](https://pypi.org/project/flask) | 2.0.0~2.2.2 |
| pymongo | [pymongo](https://pypi.org/project/pymongo) | 3.10.0~3.13.0 |
| pymysql | [pymysql](https://pypi.org/project/pymysql) | 0.9.0~0.10.1 |
| | | 1.0.0~1.0.2 |

## Baseline setup

The Lumigo OpenTelemetry Distro will automatically create the following OpenTelemetry constructs provided to a `TraceProvider`.

### Resource attributes

#### SDK resource attributes

* The attributes from the default resource:
  * `telemetry.sdk.language`: `python`
  * `telemetry.sdk.name`: `opentelemetry`
  * `telemetry.sdk.version`: depends on the version of the `opentelemetry-sdk` included in the [dependencies](./setup.py)

* The `lumigo.distro.version` containing the version of the Lumigo OpenTelemetry Distro for Python as specified in the [VERSION file](./src/lumigo_opentelemetry/VERSION)

#### Process resource attributes

* The following `process.runtime.*` attributes as specified in the [Process Semantic Conventions](https://opentelemetry.io/docs/reference/specification/resource/semantic_conventions/process/#process-runtimes):
  * `process.runtime.description`
  * `process.runtime.name`
  * `process.runtime.version`

* A non-standard `process.environ` resource attribute, containing a stringified representation of the process environment, with environment variables scrubbed based on the [`LUMIGO_SECRET_MASKING_REGEX`](#lumigo-specific-configurations) configuration.

#### Amazon ECS resource attributes

If the instrumented Python application is running on the Amazon Elastic Container Service (ECS):
  * `cloud.provider` attribute with value `aws`
  * `cloud.platform` with value `aws_ecs`
  * `container.name` with the hostname of the ECS Task container
  * `container.id` with the ID of the Docker container (based on the cgroup id)

If the ECS task uses the ECS agent v1.4.0, and has therefore access to the [Task metadata endpoint version 4](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-metadata-endpoint-v4.html), the following experimental attributes as specified in the [AWS ECS Resource Attributes](https://github.com/open-telemetry/opentelemetry-specification/blob/42081e023b3827d824c45031e3ccd19318ff3411/specification/resource/semantic_conventions/cloud_provider/aws/ecs.md) specification:

  * `aws.ecs.container.arn`
  * `aws.ecs.cluster.arn`
  * `aws.ecs.launchtype`
  * `aws.ecs.task.arn`
  * `aws.ecs.task.family`
  * `aws.ecs.task.revision`

### Span exporters

* If the `LUMIGO_TRACER_TOKEN` environment variable is set: a [BatchSpanProcessor](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L126), which uses an [`OTLPSpanExporter`](https://github.com/open-telemetry/opentelemetry-python/blob/50093f220f945ae38e769ab539c78c975e582bef/exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/trace_exporter/__init__.py#L55) to push tracing data to Lumigo
* If the `LUMIGO_DEBUG_SPANDUMP` environment variable is set: a [`SimpleSpanProcessor`](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L79), which uses an [`ConsoleSpanExporter`](https://github.com/open-telemetry/opentelemetry-python/blob/25771ecdac685a5bf7ada1da21092d2061dbfc02/opentelemetry-sdk/src/opentelemetry/sdk/trace/export/__init__.py#L415) to save to file the spans collected. Do not use this in production!

### SDK configuration

* The following [SDK environment variables](https://opentelemetry.io/docs/reference/specification/sdk-environment-variables/) are supported:
  * `OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT`
  * `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT`

  ** If the `OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT` environment variable is not set, the span attribute size limit will be taken from `OTEL_ATTRIBUTE_VALUE_LENGTH_LIMIT` environment variable. The default size limit when both are not set is 2048.  

## Advanced use cases

### Access to the TracerProvider

The Lumigo OpenTelemetry Distro provides access to the `TracerProvider` it configures (see the [Baseline setup](#baseline_setup) section for more information) through the `tracer_provider` attribute of the `lumigo_opentelemetry` package:

```python
from lumigo_opentelemetry import tracer_provider

# Do here stuff like adding span processors
```

### Ensure spans are flushed to Lumigo before shutdown

For short-running processes, the `BatchProcessor` configured by the Lumigo OpenTelemetry Distro may not ensure that the tracing data are sent to Lumigo (see the [Baseline setup](#baseline_setup) section for more information).
Through the access to the `tracer_provider`, however, it is possible to ensure that all spans are flushed to Lumigo as follows:

```python
from lumigo_opentelemetry import tracer_provider

# Do some logic

tracer_provider.force_flush()

# Now the Python process can terminate, with all the spans closed so far sent to Lumigo
```

### Consuming SQS messages with Boto3 receive_message

Messaging instrumentations that retrieve messages from queues tend to be counter-intuitive for end-users: when retrivieng one of more messages from the queue, one would natutally expect that all calls done _using data from those messages_, e.g., sending their content to a database or another queue, would result in spans that are children of the describing the retrivieng of those messages.

Consider the following scenario, which is supported by the `boto3` SQS `receive_message` instrumentation of the Lumigo OpenTelemetry Distro for Python:

```python
response = client.receive_message(...)  # Instrumentation creates a `span_0` span

for message in response.get("Messages", []):
  # The SQS.ReceiveMessage span is active in this scope
  with trace.start_as_current_span("span_1"):  # span_0 is the parent of span_1
    do_something()
```

Without the scope provided by the iterator over `response["Messages"]`, `span_1` would be without a parent span, and that would result in a separate invocation and a separate transaction in Lumigo.
