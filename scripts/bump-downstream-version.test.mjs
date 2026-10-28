import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { bumpDownstreamVersion, nextPatch } from './bump-downstream-version.mjs';
import { syncLibrary } from './sync-skills.mjs';

function project(t, kind = 'npm') {
  const root = mkdtempSync(join(tmpdir(), 'skill-version-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const git = (...args) => execFileSync('git', ['-C', root, ...args], { stdio: 'pipe' });
  git('init', '-b', 'test/skill-version');
  git('config', 'user.email', 'test@example.invalid');
  git('config', 'user.name', 'Release test');
  const write = (name, contents) => {
    mkdirSync(join(root, name, '..'), { recursive: true });
    writeFileSync(join(root, name), contents);
  };
  write('library/skill.md', 'Original skill.');
  write('README.md', 'Project docs.');
  write('package.json', JSON.stringify({ name: 'consumer', version: '0.8.1', dependencies: { example: '^1.0' } }, null, 2) + '\n');
  write('package-lock.json', JSON.stringify({ version: '0.8.1', packages: { '': { version: '0.8.1' }, 'node_modules/example': { version: '1.2.3' } } }, null, 2) + '\n');
  write('VERSION', '0.1.3\n');
  const commit = () => { git('add', '.'); git('commit', '-qm', 'Fixture snapshot'); };
  commit();
  const release = kind === 'npm' ? { kind, versionFile: 'package.json', lockFile: 'package-lock.json' } : { kind, versionFile: 'VERSION' };
  return { root, write, commit, target: { directory: 'library', legacyDirectories: ['legacy-skills'], release } };
}

test('unrelated changes do not bump a package version', t => {
  const fixture = project(t);
  fixture.write('README.md', 'Changed project docs.');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), null);
  assert.equal(JSON.parse(readFileSync(join(fixture.root, 'package.json'), 'utf8')).version, '0.8.1');
});

test('a subscribed change bumps npm metadata and both lockfile versions, preserving dependencies', t => {
  const fixture = project(t);
  fixture.write('library/skill.md', 'Updated skill.');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.8.2');
  const metadata = JSON.parse(readFileSync(join(fixture.root, 'package.json'), 'utf8'));
  const lock = JSON.parse(readFileSync(join(fixture.root, 'package-lock.json'), 'utf8'));
  assert.equal(metadata.version, '0.8.2');
  assert.deepEqual(metadata.dependencies, { example: '^1.0' });
  assert.equal(lock.version, '0.8.2');
  assert.equal(lock.packages[''].version, '0.8.2');
  assert.equal(lock.packages['node_modules/example'].version, '1.2.3');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.8.2');
  fixture.commit();
  fixture.write('library/skill.md', 'Next skill update.');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.8.3');
});

test('an untracked skill addition also creates a patch release', t => {
  const fixture = project(t);
  fixture.write('library/new.md', 'New skill.');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.8.2');
});

test('retiring a skill creates a patch release', t => {
  const fixture = project(t, 'composer');
  rmSync(join(fixture.root, 'library/skill.md'));
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.1.4');
  assert.equal(readFileSync(join(fixture.root, 'VERSION'), 'utf8'), '0.1.4\n');
  assert.equal(bumpDownstreamVersion(fixture.root, fixture.target), '0.1.4');
});

test('invalid lock metadata prevents all release-file writes', t => {
  const fixture = project(t);
  fixture.write('library/skill.md', 'Updated skill.');
  fixture.write('package-lock.json', JSON.stringify({ version: '0.8.1', packages: {} }));
  const before = readFileSync(join(fixture.root, 'package.json'), 'utf8');
  assert.throws(() => bumpDownstreamVersion(fixture.root, fixture.target), /Locally edited release version/);
  assert.equal(readFileSync(join(fixture.root, 'package.json'), 'utf8'), before);
});

test('a manually chosen release version is preserved', t => {
  const fixture = project(t, 'composer');
  fixture.write('library/skill.md', 'Updated skill.');
  fixture.write('VERSION', '0.2.0\n');
  assert.throws(() => bumpDownstreamVersion(fixture.root, fixture.target), /Locally edited release version/);
  assert.equal(readFileSync(join(fixture.root, 'VERSION'), 'utf8'), '0.2.0\n');
});

test('stable patch versioning rejects prerelease, malformed, and overflowing versions', () => {
  assert.equal(nextPatch('1.2.9'), '1.2.10');
  for (const version of ['v1.2.3', '1.2.3-beta.1', '01.2.3', '1.2', '1.2.9007199254740991']) {
    assert.throws(() => nextPatch(version), /stable x.y.z/);
  }
});

test('syncing a Laravel edit releases only its subscriber', t => {
  const laravel = project(t, 'composer');
  const javascript = project(t);
  const source = join(laravel.root, 'source');
  for (const group of ['laravel', 'nest']) {
    laravel.write(`source/skills/${group}/actions/SKILL.md`, '---\nname: actions\ndescription: Implement an operation.\n---\n\nOriginal skill.\n');
  }
  const target = (fixture, group) => ({ ...fixture.target, agents: [], groups: [group], excludeGroups: [] });
  const phpTarget = target(laravel, 'laravel');
  const jsTarget = target(javascript, 'nest');
  for (const [fixture, config] of [[laravel, phpTarget], [javascript, jsTarget]]) {
    rmSync(join(fixture.root, 'library'), { recursive: true });
    syncLibrary(source, config, fixture.root);
    fixture.commit();
  }
  laravel.write('source/skills/laravel/actions/SKILL.md', '---\nname: actions\ndescription: Implement an operation.\n---\n\nChanged Laravel guidance.\n');
  syncLibrary(source, phpTarget, laravel.root);
  syncLibrary(source, jsTarget, javascript.root);
  assert.equal(bumpDownstreamVersion(laravel.root, phpTarget), '0.1.4');
  assert.equal(bumpDownstreamVersion(javascript.root, jsTarget), null);
});
