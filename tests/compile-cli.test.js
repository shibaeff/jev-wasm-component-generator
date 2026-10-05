'use strict';

const assert = require('node:assert/strict');
const {execFile} = require('node:child_process');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const test = require('node:test');
const {promisify} = require('node:util');

const execFileAsync = promisify(execFile);

test('compile-wat emits a real WebAssembly binary when output is requested', async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'jev-wasm-'));
  const output = path.join(directory, 'component.wasm');
  const input = path.join(__dirname, '..', 'library', 'ethereum_intrinsic_gas_validator.wat');

  try {
    await execFileAsync(process.execPath, [
      path.join(__dirname, '..', 'scripts', 'compile-wat.js'),
      input,
      '--output',
      output,
    ]);
    const binary = await fs.readFile(output);
    assert.deepEqual(binary.subarray(0, 8), Buffer.from([0, 97, 115, 109, 1, 0, 0, 0]));
    assert.ok(binary.length > 8);
    await WebAssembly.compile(binary);
  } finally {
    await fs.rm(directory, {recursive: true, force: true});
  }
});
