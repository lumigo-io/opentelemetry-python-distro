from lumigo_wrapper import lumigo_wrapper

from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from fastapi import FastAPI, HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

lumigo_wrapper(lumigo_token="NOPE", service_name="FlaskTestApp", resource=app)

trace.get_tracer_provider().add_span_processor(
    SimpleSpanProcessor(
        ConsoleSpanExporter(
            out=open("spans.txt", "w"),
            # Print one span per line for ease of parsing, as the
            # file itself will not be valid JSON, it will be just a
            # sequence of JSON objects, not a list
            formatter=lambda span: span.to_json(indent=None) + "\n",
        )
    )
)


@app.get("/")
async def root():
    return {"message": "Hello FastAPI!"}


@app.get("/accounts/{account_id}")
async def account(account_id):
    if account_id == "taz":
        raise HTTPException(status_code=400, detail="400 response")

    if account_id == "blitz":
        raise HTTPException(status_code=404, detail="404 response")

    if account_id == "alcatraz_smedry":
        raise HTTPException(status_code=500, detail="500 response")

    if account_id == "kaboom":
        raise StarletteHTTPException(status_code=500, detail="500 response")

    return {"account": account_id}
