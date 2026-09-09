import fs from 'node:fs';
import path from 'node:path';

function inside(candidate, root) {
  return candidate === root || candidate.startsWith(root + path.sep);
}

export function createNewOutputDirectory(rootArg, outputArg) {
  const root = fs.realpathSync(rootArg);
  const requested = path.resolve(outputArg);
  const parentRequested = path.dirname(requested);
  const parentStat = fs.lstatSync(parentRequested);
  if (!parentStat.isDirectory() || parentStat.isSymbolicLink()) {
    throw Error('existing nonsymlink output parent required');
  }
  const parent = fs.realpathSync(parentRequested);
  const out = path.join(parent, path.basename(requested));
  if (inside(out, root)) throw Error('new output outside provider required');
  if (fs.lstatSync(out, { throwIfNoEntry: false })) throw Error('refusing existing output path or symlink');
  fs.mkdirSync(out, { recursive: false, mode: 0o700 });
  const canonical = fs.realpathSync(out);
  if (canonical !== out || inside(canonical, root)) throw Error('unsafe output resolution');
  const flags = fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | (fs.constants.O_NOFOLLOW ?? 0);
  const fd = fs.openSync(out, flags);
  const descriptorPath = `/proc/self/fd/${fd}`;
  let descriptorCanonical;
  try { descriptorCanonical = fs.realpathSync(descriptorPath); }
  catch (error) { fs.closeSync(fd); throw Error(`descriptor-backed output unavailable: ${error.message}`); }
  if (descriptorCanonical !== canonical) {
    fs.closeSync(fd);
    throw Error('created output descriptor mismatch');
  }
  return { root, out, fd, descriptorPath };
}
