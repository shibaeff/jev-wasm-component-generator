'use strict';

const assert = require('node:assert/strict');
const path = require('node:path');
const test = require('node:test');
const {loadWat} = require('../lib/wasm');

const library = name => path.join(__dirname, '..', 'library', name);

test('subscription core compiles and calculates billing', async () => {
  const wasm = await loadWat(library('subscription_core.wat'));
  assert.equal(wasm.monthly_cents(1200n, 1), 1200n);
  assert.equal(wasm.monthly_cents(1200n, 3), 100n);
  assert.equal(wasm.monthly_cents(-1n, 1), -1n);
  assert.equal(wasm.monthly_cents(10n, 9), -2n);
  assert.equal(wasm.is_due(20n, 20n, 1), 1);
  assert.equal(wasm.is_due(20n, 30n, 0), 0);
});

test('checksum module exports working FNV-1a', async () => {
  const wasm = await loadWat(library('checksum.wat'));
  new Uint8Array(wasm.memory.buffer, 0, 3).set(Buffer.from('abc'));
  assert.equal(wasm.fnv1a_32(0, 3) >>> 0, 0x1a47e90b);
});

test('integer math module compiles independently', async () => {
  const wasm = await loadWat(library('integer_math.wat'));
  assert.equal(wasm.clamp_i32(12, 0, 10), 10);
  assert.equal(wasm.clamp_i32(3, 0, 10), 3);
  assert.equal(wasm.gcd_u32(54, 24), 6);
});
