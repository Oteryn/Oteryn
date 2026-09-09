import fs from 'node:fs';
import path from 'node:path';

const NOFOLLOW = fs.constants.O_NOFOLLOW ?? 0;

function leafPath(descriptorPath, name) {
  if (!name || name === '.' || name === '..' || path.basename(name) !== name) {
    throw Error('artifact name must be a single leaf');
  }
  return path.join(descriptorPath, name);
}

function requireRegularFile(fd) {
  if (!fs.fstatSync(fd).isFile()) throw Error('artifact leaf is not a regular file');
}

export function createOwnedArtifact(descriptorPath, name) {
  const fd = fs.openSync(leafPath(descriptorPath, name),
    fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | NOFOLLOW, 0o600);
  try { requireRegularFile(fd); }
  catch (error) { fs.closeSync(fd); throw error; }
  return fd;
}

export function saveOwnedArtifact(fd, bytes) {
  requireRegularFile(fd);
  fs.ftruncateSync(fd, 0);
  const data = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes);
  let offset = 0;
  while (offset < data.length) offset += fs.writeSync(fd, data, offset, data.length - offset, offset);
  fs.fsyncSync(fd);
}

export function readOwnedArtifact(fd) {
  const ownedStat = fs.fstatSync(fd);
  if (!ownedStat.isFile()) throw Error('artifact leaf is not a regular file');
  const readFd = fs.openSync(`/proc/self/fd/${fd}`, fs.constants.O_RDONLY);
  const readStat = fs.fstatSync(readFd);
  if (!readStat.isFile() || readStat.dev !== ownedStat.dev || readStat.ino !== ownedStat.ino) {
    fs.closeSync(readFd);
    throw Error('owned artifact descriptor mismatch');
  }
  const size = readStat.size;
  const data = Buffer.alloc(size);
  try {
    let offset = 0;
    while (offset < size) {
      const count = fs.readSync(readFd, data, offset, size - offset, offset);
      if (count === 0) throw Error('short artifact read');
      offset += count;
    }
    return data;
  } finally { fs.closeSync(readFd); }
}

export function readArtifactLeaf(descriptorPath, name) {
  const fd = fs.openSync(leafPath(descriptorPath, name), fs.constants.O_RDONLY | NOFOLLOW);
  try { return readOwnedArtifact(fd); }
  finally { fs.closeSync(fd); }
}

export function publishArtifactLeaf(descriptorPath, name, bytes) {
  const fd = createOwnedArtifact(descriptorPath, name);
  try { saveOwnedArtifact(fd, bytes); }
  finally { fs.closeSync(fd); }
}

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
