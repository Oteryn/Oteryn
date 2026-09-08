#!/usr/bin/env node
// Offline reassessment of recorded DOM observations, not new browser execution.
import fs from 'node:fs';
import { evaluateReport } from './public-surface-contract.mjs';
const raw = fs.readFileSync(0);
if (raw.length > 1_000_000) throw Error('recorded browser evidence exceeds byte limit');
const assessment = evaluateReport(JSON.parse(raw.toString('utf8')));
console.log(JSON.stringify({ ...assessment, mode: 'OFFLINE_REASSESSMENT_NOT_NEW_BROWSER_EXECUTION' }));
if (assessment.errors.length) process.exitCode = 1;
