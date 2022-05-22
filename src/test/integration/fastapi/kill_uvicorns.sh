PID="$(pgrep -f uvicorn)"
if [[ -n "$PID" ]]
then
    for ID in ${PID}
    do
      kill -9 "${ID}"
    done
fi