import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const NOFOLLOW = fs.constants.O_NOFOLLOW ?? 0;
const O_TMPFILE = 0x410000;
const LINKAT_PROGRAM = String.raw`
import ctypes, os, sys
libc = ctypes.CDLL(None, use_errno=True)
linkat = getattr(libc, "linkat", None)
if linkat is None:
    raise OSError(38, "linkat unavailable")
source = os.fsencode(sys.argv[1])
name = os.fsencode(sys.argv[2])
if linkat(-100, source, 3, name, 0x400) != 0:
    error = ctypes.get_errno()
    raise OSError(error, os.strerror(error), sys.argv[2])
`;

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
  leafPath(descriptorPath, name);
  if (process.platform !== 'linux' || !NOFOLLOW) {
    throw Error('atomic owned-artifact publication unavailable');
  }
  const fd = fs.openSync(descriptorPath, fs.constants.O_RDWR | O_TMPFILE, 0o600);
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
  try { saveOwnedArtifact(fd, bytes); publishOwnedArtifact(descriptorPath, name, fd); }
  finally { fs.closeSync(fd); }
}

export function publishOwnedArtifact(descriptorPath, name, ownedFd, hooks = {}) {
  const leaf = path.basename(leafPath(descriptorPath, name));
  requireRegularFile(ownedFd);
  const directoryFd = Number(path.basename(descriptorPath));
  if (!Number.isSafeInteger(directoryFd) || descriptorPath !== `/proc/self/fd/${directoryFd}`) {
    throw Error('descriptor-backed artifact directory required');
  }
  hooks.beforePublish?.();
  const source = `/proc/${process.pid}/fd/${ownedFd}`;
  const result = spawnSync('/usr/bin/python3', ['-c', LINKAT_PROGRAM, source, leaf], {
    encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe', directoryFd],
  });
  if (result.error) throw Error(`atomic artifact publication unavailable: ${result.error.message}`);
  if (result.status !== 0) {
    const detail = (result.stderr || '').trim();
    throw Error(`atomic exclusive artifact publication failed: ${name}${detail ? `: ${detail}` : ''}`);
  }
}

function inside(candidate, root) {
  return candidate === root || candidate.startsWith(root + path.sep);
}

export function createNewOutputDirectory(rootArg, outputArg, hooks = {}) {
  const root = fs.realpathSync(rootArg);
  const requested = path.resolve(outputArg);
  const parentRequested = path.dirname(requested);
  const parentStat = fs.lstatSync(parentRequested);
  if (!parentStat.isDirectory() || parentStat.isSymbolicLink()) {
    throw Error('existing nonsymlink output parent required');
  }
  const flags = fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | (fs.constants.O_NOFOLLOW ?? 0);
  if (!fs.constants.O_NOFOLLOW || !fs.existsSync('/proc/self/fd')) {
    throw Error('descriptor-relative output creation unavailable');
  }
  const parentFd = fs.openSync(parentRequested, flags);
  let fd;
  try {
    const openedParent = fs.fstatSync(parentFd);
    if (openedParent.dev !== parentStat.dev || openedParent.ino !== parentStat.ino) {
      throw Error('output parent changed during validation');
    }
    const parentDescriptorPath = `/proc/self/fd/${parentFd}`;
    const parent = fs.realpathSync(parentDescriptorPath);
    if (inside(parent, root)) throw Error('new output outside provider required');
    hooks.afterParentOpened?.({ parentFd, parent, parentDescriptorPath });
    const leaf = path.basename(requested);
    const descriptorOut = leafPath(parentDescriptorPath, leaf);
    if (fs.lstatSync(descriptorOut, { throwIfNoEntry: false })) throw Error('refusing existing output path or symlink');
    fs.mkdirSync(descriptorOut, { recursive: false, mode: 0o700 });
    fd = fs.openSync(descriptorOut, flags);
  } finally { fs.closeSync(parentFd); }
  const descriptorPath = `/proc/self/fd/${fd}`;
  let descriptorCanonical;
  try { descriptorCanonical = fs.realpathSync(descriptorPath); }
  catch (error) { fs.closeSync(fd); throw Error(`descriptor-backed output unavailable: ${error.message}`); }
  if (inside(descriptorCanonical, root)) { fs.closeSync(fd); throw Error('unsafe output resolution'); }
  return { root, out: descriptorCanonical, fd, descriptorPath };
}
