'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');
const {loadWat} = require('../lib/wasm');

const fixture = name => path.join(__dirname, '..', 'examples', 'sort-evolution', name);

async function checkSort(filename) {
  const wasm = await loadWat(fixture(filename));
  const cases = [
    [], [7], [2, 1], [1, 2, 3, 4], [4, 3, 2, 1],
    [5, -1, 5, 0, -9, 5],
    [-2147483648, 2147483647, 0, -1, 1],
  ];
  for (const values of cases) {
    const offset = 16;
    const view = new DataView(wasm.memory.buffer);
    view.setUint32(offset - 4, 0xdeadbeef, true);
    view.setUint32(offset + values.length * 4, 0xcafebabe, true);
    values.forEach((value, index) => view.setInt32(offset + index * 4, value, true));
    wasm.sort(offset, values.length);
    const actual = values.map((_, index) => view.getInt32(offset + index * 4, true));
    const expected = [...values].sort((a, b) => a - b);
    assert.deepEqual(actual, expected, `${filename}: ${values}`);
    assert.equal(view.getUint32(offset - 4, true), 0xdeadbeef);
    assert.equal(view.getUint32(offset + values.length * 4, true), 0xcafebabe);
  }
}

test('insertion-sort baseline sorts signed i32 values in place', async () => {
  await checkSort('insertion_sort.wat');
});

test('evolved quicksort sorts signed i32 values in place', async () => {
  await checkSort('quicksort.wat');
});
