export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

uv sync

uv run python -m unittest discover -s tests -v

uv run python evaluate.py --baseline --run-id pilot-01

uv run python evaluate.py --candidate \
  --run-id pilot-01 \
  --description "Ridge inicial alpha=10"
