# Insertion sort → quicksort by structured WAT edits

This example starts from a complete, compiling insertion-sort module and iteratively transforms it into a complete, compiling quicksort module.

```sh
./jev-wasm-evolve --model jev-latest \
  --initial examples/sort-evolution/insertion_sort.wat \
  --target examples/sort-evolution/quicksort.wat \
  --output generated/evolved-sort.wat \
  --trace generated/evolution-trace.json \
  "transition insertion sort to quicksort while preserving sort(offset, length)"
```

The model receives the full current and target WAT at every iteration. It ranks only opaque, structured operations:

```text
insert(position, WAT block)
replace(position, delete_count=1, WAT block)
remove(position, delete_count=1)
END
```

The demonstrated path is:

1. Insert `$swap` at block position 1.
2. Insert `$partition` at block position 2.
3. Insert recursive `$quicksort` at block position 3.
4. Replace the exported insertion-sort wrapper at position 5 with the quicksort wrapper.
5. Remove the now-unused insertion-sort helper at position 4.
6. Select `END` only after an exact target match.

Every intermediate full program compiles. Both endpoints pass signed-i32, duplicate, boundary, empty-array, singleton, and memory-canary tests.

This is **reference-guided transformation**, because the complete quicksort target is supplied. It is not novel synthesis.
