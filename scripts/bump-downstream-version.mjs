import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { inside, targets } from './sync-skills.mjs';

const STABLE_VERSION = /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/;

export function nextPatch(version) {
  const match = STABLE_VERSION.exec(version);
  if (!match || match.slice(1).some(part => !Number.isSafeInteger(Number(part))) || !Number.isSafeInteger(Number(match[3]) + 1)) {
    throw new Error(`Expected a stable x.y.z release version, received: ${version}`);
  }
  return `${match[1]}.${match[2]}.${Number(match[3]) + 1}`;
}

function git(checkout, ...args) {
  return execFileSync('git', ['-C', checkout, ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
}

/** Compare only the subscribed snapshot; unrelated edits never create a release. */
export function bumpDownstreamVersion(checkout, target) {
  const owned = [target.directory, ...target.legacyDirectories];
  for (const file of owned) inside(checkout, file);
  if (!git(checkout, 'status', '--porcelain', '--untracked-files=all', '--', ...owned.map(file => `:(literal)${file}`)).trim()) return null;

  const release = target.release;
  if (!release || !['npm', 'composer'].includes(release.kind)) throw new Error('Unsupported downstream release configuration');
  const versionPath = inside(checkout, release.versionFile);
  const baseline = git(checkout, 'show', `HEAD:${release.versionFile}`);
  const current = release.kind === 'npm' ? JSON.parse(baseline).version : baseline.trim();
  const next = nextPatch(current);
  const pending = new Map();
  const validWorkingVersion = value => {
    if (value !== current && value !== next) throw new Error(`Locally edited release version would be overwritten: ${value}`);
  };

  if (release.kind === 'npm') {
    const metadata = JSON.parse(readFileSync(versionPath, 'utf8'));
    validWorkingVersion(metadata.version);
    metadata.version = next;
    pending.set(versionPath, `${JSON.stringify(metadata, null, 2)}\n`);
    const lockPath = inside(checkout, release.lockFile);
    const lock = JSON.parse(readFileSync(lockPath, 'utf8'));
    validWorkingVersion(lock.version);
    validWorkingVersion(lock.packages?.['']?.version);
    lock.version = next;
    lock.packages[''].version = next;
    pending.set(lockPath, `${JSON.stringify(lock, null, 2)}\n`);
  } else {
    validWorkingVersion(readFileSync(versionPath, 'utf8').trim());
    pending.set(versionPath, `${next}\n`);
  }

  // Validate every file before changing any version metadata. Read HEAD so retries
  // update the same pending release rather than incrementing the version twice.
  for (const [file, contents] of pending) writeFileSync(file, contents);
  return next;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [name, checkout] = process.argv.slice(2);
  const target = targets()[name];
  if (!target || !checkout) throw new Error('Usage: node scripts/bump-downstream-version.mjs <target> <checkout>');
  const version = bumpDownstreamVersion(resolve(checkout), target);
  console.log(version ? `Prepared patch release ${version}.` : 'No subscribed file changes; release version unchanged.');
}
