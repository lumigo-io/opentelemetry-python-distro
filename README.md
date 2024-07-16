# Lumigo OpenTelemetry Distro for Python :stars:

[![Tracer Testing](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml/badge.svg)](https://github.com/lumigo-io/opentelemetry-python-distro/actions/workflows/push-actions.yml)
![Version](https://badge.fury.io/py/lumigo_opentelemetry.svg)

The Lumigo OpenTelemetry Distribution for Python is a package that provides no-code distributed tracing for containerized applications.

The Lumigo OpenTelemetry Distribution for Python is made of several upstream OpenTelemetry packages, with additional automated quality-assurance and customizations that optimize for no-code injection, meaning that you should need to update exactly zero lines of code in your application in order to make use of the Lumigo OpenTelemetry Distribution.
(See the [No-code activation](#no-code-activation) section for auto-instrumentation instructions)

## Logging support
The Lumigo OpenTelemetry Distribution also allows logging span-correlated records. See the [configuration](#logging-instrumentation) section for details on how to enable this feature.
When using the logging feature, the same set of rules for [secret masking](#lumigo-specific-configurations) applies on the content of the log message, with only `LUMIGO_SECRET_MASKING_REGEX` being considered.

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

**Note:** The instructions in this section are mutually exclusive with those provided in the [Manual activation](#manual-activation) section.

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

* [General configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/configuration/sdk-environment-variables.md#general-sdk-configuration)
* [Batch span processor configurations](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/configuration/sdk-environment-variables.md#batch-span-processor): The Lumigo OpenTelemetry Distro for Python uses a batch processor for sending data to Lumigo.

### Lumigo-specific configurations

The `lumigo_opentelemetry` package additionally supports the following configuration options as environment variables:

* `LUMIGO_TRACER_TOKEN`: [Required] Required configuration to send data to Lumigo; you will find the right value in Lumigo under `Settings -> Tracing -> Manual tracing`.
* `LUMIGO_DEBUG=true`: Enables debug logging
* `LUMIGO_DEBUG_SPANDUMP`: path to a local file where to write a local copy of the spans that will be sent to Lumigo; this option handy for local testing but **should not be used in production** unless you are instructed to do so by Lumigo support.
* `LUMIGO_SECRET_MASKING_REGEX=["regex1", "regex2"]`: Prevents Lumigo from sending keys that match the supplied regular expressions. All regular expressions are case-insensitive. By default, Lumigo applies the following regular expressions: `[".*pass.*", ".*key.*", ".*secret.*", ".*credential.*", ".*passphrase.*"]`.
  * We support more granular masking using the following parameters. If not given, the above configuration is the fallback: `LUMIGO_SECRET_MASKING_REGEX_HTTP_REQUEST_BODIES`, `LUMIGO_SECRET_MASKING_REGEX_HTTP_REQUEST_HEADERS`, `LUMIGO_SECRET_MASKING_REGEX_HTTP_RESPONSE_BODIES`, `LUMIGO_SECRET_MASKING_REGEX_HTTP_RESPONSE_HEADERS`, `LUMIGO_SECRET_MASKING_REGEX_HTTP_QUERY_PARAMS`, `LUMIGO_SECRET_MASKING_REGEX_ENVIRONMENT`.
* `LUMIGO_SWITCH_OFF=true`: This option disables the Lumigo OpenTelemetry distro entirely; no instrumentation will be injected, no tracing data will be collected.
* `LUMIGO_REPORT_DEPENDENCIES=false`: This option disables the built-in dependency reporting to Lumigo SaaS. For more information, refer to the [Automated dependency reporting](#automated-dependency-reporting) section.
* `LUMIGO_AUTO_FILTER_EMPTY_SQS`: This option enables the automatic filtering of empty SQS messages from being sent to Lumigo SaaS. For more information, refer to the [Filtering out empty SQS messages](#filtering-out-empty-sqs-messages) section.
* `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX='["regex1", "regex2"]'`: This option enables the filtering of client and server endpoints through regular expression searches. Fine-tune your settings via the following environment variables, which work in conjunction with `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX` for a specific span type:
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER` applies the regular expression search exclusively to server spans. Searching is performed against the following attributes on a span: `url.path` and `http.target`.
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT` applies the regular expression search exclusively to client spans. Searching is performed against the following attributes on a span: `url.full` and `http.url`.

  For more information check out [Filtering http endpoints](#filtering-http-endpoints).

#### Logging instrumentation

* `LUMIGO_ENABLE_LOGS` - Default: `false`. When set to `true`, turns on the `logging` instrumentation to capture log-records logged by Python's `logging` builtin library and send them to Lumigo. Emitted logs will also get injected with the active span context (see [list](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/logging/logging.html#module-opentelemetry.instrumentation.logging)).

* `LUMIGO_DEBUG_LOGDUMP` - similar to `LUMIGO_DEBUG_SPANDUMP`, only for logs instead of spans. Effective only when `LUMIGO_ENABLE_LOGS` is set to `true`.

### Execution Tags

[Execution Tags](https://docs.lumigo.io/docs/execution-tags) allow you to dynamically add dimensions to your invocations so that they can be identified, searched for, and filtered in Lumigo.
For example: in multi-tenanted systems, execution tags are often used to mark with the identifiers of the end-users that trigger them for analysis (e.g., [Explore view](https://docs.lumigo.io/docs/explore)) and alerting purposes.

#### Creating Execution Tags

In the Lumigo OpenTelemetry Distro for Python, execution tags are represented as [span attributes](https://opentelemetry.io/docs/reference/specification/common/#attribute) and, specifically, as span attributes with the `lumigo.execution_tags.` prefix.
For example, you could add an execution tag as follows:

```python
from opentelemetry.trace import get_current_span

get_current_span().set_attribute('lumigo.execution_tags.foo','bar')
```

Notice that, using OpenTelemetry's [`get_current_span()` API](https://opentelemetry.io/docs/instrumentation/python/manual/#get-the-current-span), you do not need to keep track of the current span, you can get it at any point of your program execution.

In OpenTelemetry, span attributes can be `strings`, `numbers` (double precision floating point or signed 64 bit integer), `booleans` (a.k.a. "primitive types"), and arrays of one primitive type (e.g., an array of string, and array of numbers or an array of booleans).
In Lumigo, booleans and numbers are transformed to strings.

**IMPORTANT:** If you use the `Span.set_attribute` API multiple times _on the same span_ to set values for the same key multiple values, you may override previous values rather than adding to them:

```python
from opentelemetry.trace import get_current_span

get_current_span().set_attribute('lumigo.execution_tags.foo','bar')
get_current_span().set_attribute('lumigo.execution_tags.foo','baz')
```

In the snippets above, the `foo` execution tag will have in Lumigo only the `baz` value!
Multiple values for an execution tag are supported as follows:

```python
from opentelemetry.trace import get_current_span

get_current_span().set_attribute('lumigo.execution_tags.foo',['bar', 'baz'])
```

Tuples are also supported to specify multiple values for an execution tag:

```python
from opentelemetry.trace import get_current_span

get_current_span().set_attribute('lumigo.execution_tags.bar',('baz','xyz',))
```

The snippets above will produce in Lumigo the `foo` tag having both `bar` and `baz` values.
Another option to set multiple values is setting [execution Tags in different spans of an invocation](#execution-tags-in-different-spans-of-an-invocation).

#### Execution Tags in different spans of an invocation

In Lumigo, multiple spans may be merged together into one invocation, which is the entry that you see, for example, in the [Explore view](https://docs.lumigo.io/docs/explore).
The invocation will include all execution tags on all its spans, and merge their values:

```python
from opentelemetry import trace

trace.get_current_span().set_attribute('lumigo.execution_tags.foo','bar')

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span('child_span') as child_span:
    child_span.set_attribute('lumigo.execution_tags.foo','baz')
```

In the examples above, the invocation in Lumigo resulting from executing the code will have both `bar` and `baz` values associated with the `foo` execution tag.
Which spans are merged in the same invocation depends on the parent-child relations among those spans.
Explaining this topic is outside the scope of this documentation; a good first read to get deeper into the topic is the [Traces](https://opentelemetry.io/docs/concepts/signals/traces/) documentation of OpenTelemetry.
In case your execution tags on different spans appear on different invocations than what you would expect, get in touch with [Lumigo support](https://docs.lumigo.io/docs/support).

#### Execution Tag Limitations

* Up to 50 execution tag keys per invocation in Lumigo, irrespective of how many spans are part of the invocation or how many values each execution tag has.
* The `key` of an execution tag cannot contain the `.` character; for example: `lumigo.execution_tags.my.tag` is not a valid tag. The OpenTelemetry `Span.set_attribute()` API will not fail or log warnings, but that will be displayed as `my` in Lumigo.
* Each execution tag key can be at most 50 characters long; the `lumigo.execution_tags.` prefix does _not_ count against the 50 characters limit.
* Each execution tag value can be at most 70 characters long.

### Programmatic Errors

[Programmatic Errors](https://docs.lumigo.io/docs/programmatic-errors) allow you to customize errors, monitor and troubleshoot issues that should not necessarily interfere with the service.
For example, an application tries to remove a user who doesn't exist. These custom errors can be captured by adding just a few lines of additional code to your application.

Programmatic Errors indicating that a non-fatal error occurred, such as an application error. You can log programmatic errors, track custom error issues, and trigger [Alerts](https://docs.lumigo.io/docs/event-alert).

#### Creating a Programmatic Error

Programmatic errors are created by adding [span events](https://opentelemetry.io/docs/instrumentation/python/manual/#adding-events) with a custom attribute being set with the key name `lumigo.type`.

For example, you could add a programmatic error as follows:

```python
from opentelemetry.trace import get_current_span

get_current_span().add_event('<error-message>', {'lumigo.type': '<error-type>'})
```

## Supported runtimes

* cpython: 3.7.x, 3.8.x, 3.9.x, 3.10.x, 3.11.x

## Supported packages

| Instrumentation | Package | Supported Versions | | | | |
| --- | --- | :---: | :---: | :---: | :---: | :---: |
| | | 3.7 | 3.8 | 3.9 | 3.10 | 3.11 |
| botocore | [boto3](https://pypi.org/project/boto3) | 1.17.22~1.33.13|1.17.22~1.34.144|1.17.22~1.34.144|1.17.22~1.34.144|1.17.22~1.34.144|
| django | [django](https://pypi.org/project/django) | 3.2.1~3.2.25|3.2.1~3.2.25|3.2.1~3.2.25|3.2.1~3.2.25|3.2.1~3.2.25|
| | | 3.2| 4.0.1~4.2.14| 4.0.1~4.2.14| 4.0.1~4.2.14| 4.0.1~4.2.14|
| | | | 3.2| 3.2| 5.0.1~5.1.1| 5.0.1~5.1.1|
| | | | 4.0| 4.0| 3.2| 3.2|
| | | | 4.0.a1| 4.0.a1| 4.0| 4.0|
| | | | 4.0.b1| 4.0.b1| 4.0.a1| 4.0.a1|
| | | | 4.0.rc1| 4.0.rc1| 4.0.b1| 4.0.b1|
| | | | 4.1| 4.1| 4.0.rc1| 4.0.rc1|
| | | | 4.1.a1| 4.1.a1| 4.1| 4.1|
| | | | 4.1.b1| 4.1.b1| 4.1.a1| 4.1.a1|
| | | | 4.1.rc1| 4.1.rc1| 4.1.b1| 4.1.b1|
| | | | 4.1rc1| 4.1rc1| 4.1.rc1| 4.1.rc1|
| | | | 4.2| 4.2| 4.1rc1| 4.1rc1|
| | | | 4.2.a1| 4.2.a1| 4.2| 4.2|
| | | | 4.2.b1| 4.2.b1| 4.2.a1| 4.2.a1|
| | | | 4.2.rc1| 4.2.rc1| 4.2.b1| 4.2.b1|
| | | | 4.2rc1| 4.2rc1| 4.2.rc1| 4.2.rc1|
| | | | | | 4.2rc1| 4.2rc1|
| | | | | | 5.0| 5.0|
| | | | | | 5.0rc1| 5.0rc1|
| fastapi | [uvicorn](https://pypi.org/project/uvicorn) | 0.11.3~0.22.0|0.11.3~0.22.0|0.11.3~0.22.0|0.11.3~0.22.0|0.12.0~0.22.0|
| | | | 0.24.0~0.30.1| 0.24.0~0.30.1| 0.24.0~0.30.1| 0.24.0~0.30.1|
|  | [fastapi](https://pypi.org/project/fastapi) | 0.56.1~0.100.0|0.56.1~0.100.0|0.56.1~0.100.0|0.56.1~0.100.0|0.56.1~0.100.0|
| | | 0.100.0b2~0.103.2| 0.100.0b2~0.111.1| 0.100.0b2~0.111.1| 0.100.0b2~0.111.1| 0.100.0b2~0.111.1|
| flask | [flask](https://pypi.org/project/flask) | 2.0.0~2.2.5|2.0.0~2.2.5|2.0.0~2.2.5|2.0.0~2.2.5|2.0.0~2.2.5|
| grpcio | [grpcio](https://pypi.org/project/grpcio) | 1.45.0~1.62.2|1.45.0~1.65.0rc2|1.45.0~1.65.0rc2|1.45.0~1.65.0rc2|1.49.0~1.65.0rc2|
| kafka_python | [kafka_python](https://pypi.org/project/kafka_python) | 2.0.0~2.0.2|2.0.0~2.0.2|2.0.0~2.0.2|2.0.0~2.0.2|2.0.0~2.0.2|
| pika | [pika](https://pypi.org/project/pika) | 1.0.0|1.0.0|1.0.0|1.0.0|1.0.0|
| | | 1.0.1~1.3.0| 1.0.1~1.3.0| 1.0.1~1.3.0| 1.0.1~1.3.0| 1.0.1~1.3.0|
| | | 1.3.0rc5~1.3.2| 1.3.0rc5~1.3.2| 1.3.0rc5~1.3.2| 1.3.0rc5~1.3.2| 1.3.0rc5~1.3.2|
| psycopg | [psycopg](https://pypi.org/project/psycopg) | 3.1.1~3.1.20|3.1.1~3.2.1|3.1.1~3.2.1|3.1.1~3.2.1|3.1.1~3.2.1|
| | | 3.1| 3.1| 3.1| 3.1| 3.1|
|  | [psycopg-binary](https://pypi.org/project/psycopg-binary) | 3.1.1~3.1.20|3.1.1~3.2.1|3.1.1~3.2.1|3.1.1~3.2.1|3.1.4~3.2.1|
| | | 3.1| 3.1| 3.1| 3.1| |
| psycopg2 | [psycopg2](https://pypi.org/project/psycopg2) | 2.7.5~2.9.9|2.8.1~2.9.9|2.8.1~2.9.9|2.8.1~2.8.6|2.9.5~2.9.9|
| | | 2.8| 2.8| 2.8| 2.9.5~2.9.9| |
| | | 2.9| 2.9| 2.9| 2.8| |
|  | [psycopg2-binary](https://pypi.org/project/psycopg2-binary) | 2.7.5~2.9.9|2.8.1~2.9.9|2.8.1~2.9.9|2.8.1~2.8.6|2.9.5~2.9.9|
| | | 2.8| 2.8| 2.8| 2.9.5~2.9.9| |
| | | 2.9| 2.9| 2.9| 2.8| |
| pymongo | [pymongo](https://pypi.org/project/pymongo) | 3.1.1~3.3.1|3.1.1~3.3.1|3.1.1~3.3.1|3.1.1~3.3.1|3.1.1~3.3.1|
| | | 3.5.0~3.13.0| 3.5.0~3.13.0| 3.5.0~3.13.0| 3.5.0~3.13.0| 3.5.0~3.13.0|
| | | 4.0.1~4.7.3| 4.0.1~4.8.0b0| 4.0.1~4.8.0b0| 4.0.1~4.8.0b0| 4.0.1~4.8.0b0|
| | | 3.1| 3.1| 3.1| 3.1| 3.1|
| | | 3.2| 3.2| 3.2| 3.2| 3.2|
| | | 4.0| 4.0| 4.0| 4.0| 4.0|
| pymysql | [pymysql](https://pypi.org/project/pymysql) | 0.9.0~0.10.1|0.9.0~0.10.1|0.9.0~0.10.1|0.9.0~0.10.1|0.9.0~0.10.1|
| | | 1.0.0~1.0.3| 1.0.0~1.0.3| 1.0.0~1.0.3| 1.0.0~1.0.3| 1.0.0~1.0.3|
| | | 1.1.0~1.1.1| 1.1.0~1.1.1| 1.1.0~1.1.1| 1.1.0~1.1.1| 1.1.0~1.1.1|
| redis | [redis](https://pypi.org/project/redis) | 4.1.1~4.2.0|4.1.1~4.2.0|4.1.1~4.2.0|4.1.1~4.2.0|4.1.1~4.2.0|
| | | 4.2.1~4.6.0| 4.2.1~4.6.0| 4.2.1~4.6.0| 4.2.1~4.6.0| 4.2.1~4.6.0|
| | | 5.0.0~5.1.0a1| 5.0.0~5.1.0b7| 5.0.0~5.1.0b7| 5.0.0~5.1.0b7| 5.0.0~5.1.0b7|

## Automated dependency reporting

To provide better support and better data-driven product decisions with respect to which packages to support next, the Lumigo OpenTelemetry Distro for Python will report to Lumigo SaaS on startup the packages and their versions used in this application, together with the OpenTelemetry resource data to enable analytics in terms of which platforms use which dependencies.

The data uploaded to Lumigo is a set of key-value pairs with package name and version.
Similar is available through the tracing data sent to Lumigo, except that this aims at covering dependencies for which the Lumigo OpenTelemetry Distro for Python does not have instrumentation (yet?).
Lumigo's only goal for these analytics data is to be able to give you the instrumentations you need without you needing to tell us!

The dependencies data is sent only when a `LUMIGO_TRACER_TOKEN` is present in the process environment, and it can be opted out via the `LUMIGO_REPORT_DEPENDENCIES=false` environment variable.

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

#### Kubernetes resource attributes

* `k8s.pod.uid` with the Pod identifier, supported for both cgroups v1 and v2

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

The Lumigo OpenTelemetry Distro provides access to the `TracerProvider` it configures (see the [Baseline setup](#baseline-setup) section for more information) through the `tracer_provider` attribute of the `lumigo_opentelemetry` package:

```python
from lumigo_opentelemetry import tracer_provider

# Do here stuff like adding span processors
```

### Ensure spans are flushed to Lumigo before shutdown

For short-running processes, the `BatchProcessor` configured by the Lumigo OpenTelemetry Distro may not ensure that the tracing data are sent to Lumigo (see the [Baseline setup](#baseline-setup) section for more information).
Through the access to the `tracer_provider`, however, it is possible to ensure that all spans are flushed to Lumigo as follows:

```python
from lumigo_opentelemetry import tracer_provider

# Do some logic

tracer_provider.force_flush()

# Now the Python process can terminate, with all the spans closed so far sent to Lumigo
```

### Consuming SQS messages with Boto3 receive_message

Messaging instrumentations that retrieve messages from queues tend to be counter-intuitive for end-users: when retrieving one or more messages from the queue, one would naturally expect that all calls done _using data from those messages_, e.g., sending their content to a database or another queue, would result in spans that are children of the describing the retrieving of those messages.

Consider the following scenario, which is supported by the `boto3` SQS `receive_message` instrumentation of the Lumigo OpenTelemetry Distro for Python:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

response = client.receive_message(...)  # Instrumentation creates a `span_0` span

for message in response.get("Messages", []):
  # The SQS.ReceiveMessage span is active in this scope
  with tracer.start_as_current_span("span_1"):  # span_0 is the parent of span_1
    do_something()
```

Without the scope provided by the iterator over `response["Messages"]`, `span_1` would be without a parent span, and that would result in a separate invocation and a separate transaction in Lumigo.

### Filtering out empty SQS messages

A common pattern in SQS-based applications is to continuously poll an SQS queue for messages,
and to process them as they arrive.
In order not to clutter the Lumigo platform with empty SQS polling messages, the default behavior is to filter them
out from being sent to Lumigo.

You can change this behavior by setting the boolean environment variable `LUMIGO_AUTO_FILTER_EMPTY_SQS` to `false`.
The possible variations are:

* `LUMIGO_AUTO_FILTER_EMPTY_SQS=true` filter out empty SQS polling messages
* `LUMIGO_AUTO_FILTER_EMPTY_SQS=false` do not filter out empty SQS polling messages
* No environment variable set (default): filter out empty SQS polling messages

### Filtering http endpoints

You can selectively filter spans based on HTTP server/client endpoints for various components, not limited to web frameworks.

#### Global filtering
Set the `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX` environment variable to a list of regex strings. Spans with matching server/client endpoints will not be traced.

#### Specific Filtering
For exclusive server (inbound) or client (outbound) span filtering, use the environment variables:
* `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER`
* `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT`

Notes:
* the environment variable must be a valid JSON array of strings, so if you want to match endpoint with the hostname `google.com` the environment variable value should be `["google\\.com"]`.
* If we are filtering out an HTTP call to an opentelemetry traced component, every subsequent invocation made by that
component won't be traced either.

Examples:
* Filtering out every incoming HTTP request to the `/login` endpoint (will also match requests such as `/login?user=foo`, `/login/bar`))):
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_SERVER=["\\/login"]`
* Filtering out every outgoing HTTP request to the `google.com` domain (will also match requests such as `google.com/foo`, `bar.google.com`):
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT=["google\\.com"]`'
* Filtering out every outgoing HTTP request to `https://www.google.com` (will also match requests such as `https://www.google.com/`, `https://www.google.com/foo`)
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX_CLIENT=["https:\\/\\/www\\.google\\.com"]`
* Filtering out every HTTP request (incoming or outgoing) with the word `login`:
  * `LUMIGO_FILTER_HTTP_ENDPOINTS_REGEX=["login"]`

## Contributing

For guidelines on contributing, please see [CONTRIBUTING.md](./CONTRIBUTING.md).
