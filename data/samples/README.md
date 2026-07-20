# Data samples

Truncated previews of the 8 core tables, first 200 rows of each, in both the
raw (`bronze`-equivalent, as-generated) and `silver` (cleaned) form. These let
you inspect schema, column types, and the effect of the cleaning step without
pulling the full dataset.


## Full dataset

The complete tables (`data/raw/`, `data/silver/`) are gitignored — roughly
270 MB across ~2.36M rows, all synthetic and deterministic from a fixed seed.


See [docs/README.md](../../docs/README.md)
for the column dictionary.
