#!/usr/bin/env node
'use strict';

const fs = require('node:fs/promises');
const {compileWat} = require('../lib/wasm');

const args = process.argv.slice(2);
const outputIndex = args.indexOf('--output');
const valid =
  (args.length === 1 && outputIndex === -1) ||
  (args.length === 3 && outputIndex === 1 && args[2]);

if (!valid) {
  process.stderr.write('usage: compile-wat.js FILE.wat [--output FILE.wasm]\n');
  process.exit(2);
}

const input = args[0];
const output = outputIndex === -1 ? null : args[2];

compileWat(input).then(async binary => {
  if (output) {
    await fs.writeFile(output, binary);
    process.stdout.write(`WASM written to ${output}\n`);
  } else {
    process.stdout.write('WAT compile passed\n');
  }
}).catch(error => {
  process.stderr.write(error.message + '\n');
  process.exit(1);
});
