#!/usr/bin/env node
'use strict';

const {compileWat} = require('../lib/wasm');

if (process.argv.length !== 3) {
  process.stderr.write('usage: compile-wat.js FILE.wat\n');
  process.exit(2);
}
compileWat(process.argv[2]).then(() => process.stdout.write('WAT compile passed\n')).catch(error => {
  process.stderr.write(error.message + '\n');
  process.exit(1);
});
