'use strict';

const fs = require('node:fs/promises');
const wabtFactory = require('wabt');

let wabtPromise;

async function compileWat(filename) {
  if (!wabtPromise) wabtPromise = wabtFactory();
  const [wabt, source] = await Promise.all([wabtPromise, fs.readFile(filename, 'utf8')]);
  const parsed = wabt.parseWat(filename, source, {features: {multi_value: true}});
  try {
    parsed.resolveNames();
    parsed.validate();
    return Buffer.from(parsed.toBinary({canonicalize_lebs: true}).buffer);
  } finally {
    parsed.destroy();
  }
}

async function loadWat(filename, imports = {}) {
  const binary = await compileWat(filename);
  const result = await WebAssembly.instantiate(binary, imports);
  return result.instance.exports;
}

module.exports = {compileWat, loadWat};
