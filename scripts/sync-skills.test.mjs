import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, posix } from 'node:path';
import test from 'node:test';
import { buildLibrary, SOURCE_ROOT, syncLibrary, targets } from './sync-skills.mjs';

const config = targets();
const build = name => buildLibrary(SOURCE_ROOT, config[name]);
const manifest = files => JSON.parse(files.get('catalog.json'));

test('both consumers receive a complete factory, with eight agents for each host', () => {
  for (const name of Object.keys(config)) {
    const files = build(name);
    const factory = manifest(files).items.find(item => item.name === 'factory');
    assert.ok(factory);
    assert.equal(manifest(files).schema, 2);
    for (const host of ['.agents/skills']) {
      for (const local of ['SKILL.md', 'AGENT.md', 'agents/openai.yaml', 'references/skills.md']) {
        assert.ok(files.has(factory.files[`${host}/factory/${local}`]));
      }
      assert.ok(factory.files[`${host}/catalog.md`]);
    }
    assert.equal(factory.links['.claude/skills/factory'], '.agents/skills/factory');
    assert.equal(factory.links['.ai/skills/factory'], name === 'laracanon' ? '.agents/skills/factory' : undefined);
    for (const [host, extension] of [['claude', 'md'], ['codex', 'toml']]) {
      assert.equal(Object.keys(factory.files).filter(file => file.startsWith(`.${host}/agents/`) && file.endsWith(extension)).length, 8);
    }
    assert.match(files.get('agents/factory/SKILL.md'), /disable-model-invocation: true/);
    assert.match(files.get('agents/factory/agents/openai.yaml'), /allow_implicit_invocation: false/);
  }
});

test('Laravel goes only to Laracanon; every other active group goes only to domain-driver', () => {
  for (const [name, group, absent] of [['laracanon', 'laravel', 'nest'], ['domain-driver', 'nest', 'laravel']]) {
    const files = build(name);
    const items = manifest(files).items;
    assert.ok(items.some(item => item.name === `${group}-actions`));
    assert.ok(![...files.keys()].some(file => file.startsWith(`skills/${absent}/`)));
    assert.ok(!items.some(item => item.name.startsWith(`${absent}-`)));
    assert.ok(![...files.keys()].some(file => file.startsWith('archive/')));
    assert.ok(!files.get('skills/catalog.md').includes(`| ${absent}/`));
  }
  for (const group of ['frontend', 'quality', 'javascript', 'next', 'tanstack-start']) {
    assert.ok([...build('domain-driver').keys()].some(file => file.startsWith(`skills/${group}/`)));
    assert.ok(![...build('laracanon').keys()].some(file => file.startsWith(`skills/${group}/`)));
  }
});

test('all manifest files resolve and native skill names avoid stack collisions', () => {
  for (const name of Object.keys(config)) {
    const files = build(name);
    const destinations = new Set();
    for (const item of manifest(files).items) {
      for (const [destination, source] of Object.entries(item.files)) {
        assert.ok(files.has(source), source);
        assert.ok(!destinations.has(destination), destination);
        destinations.add(destination);
        if (destination.endsWith('/SKILL.md')) assert.match(files.get(source), new RegExp(`^---\\nname: ${item.name}\\n`));
      }
    }
    const factory = manifest(files).items.find(item => item.name === 'factory');
    for (const host of ['.agents/skills']) {
      assert.ok(factory.files[posix.normalize(`${host}/factory/../../skills/catalog.md`)]);
      assert.ok(factory.files[posix.normalize(`${host}/factory/references/../../../skills/catalog.md`)]);
    }
    for (const item of manifest(files).items) {
      for (const [alias, target] of Object.entries(item.links)) {
        assert.match(alias, /^\.(?:ai|claude)\/skills\/[^/]+$/);
        assert.equal(target, `.agents/skills/${posix.basename(alias)}`);
        assert.ok(Object.keys(item.files).some(file => file === target || file.startsWith(`${target}/`)));
      }
      assert.ok(Object.keys(item.files).every(file => !file.startsWith('.ai/skills/') && !file.startsWith('.claude/skills/')));
    }
  }
});

test('supporting templates stay beside their skill, rather than overwriting application config', () => {
  const files = build('laracanon');
  const items = manifest(files).items;
  for (const [name, suffix] of [['laravel-insights', 'insights.php'], ['laravel-phpstan', 'phpstan.neon'], ['laravel-api-responses', 'templates/ApiResponse.php']]) {
    assert.ok(items.find(item => item.name === name).files[`.agents/skills/${name}/${suffix}`]);
  }
  assert.ok(items.every(item => Object.keys(item.files).every(file => file.startsWith('.'))));
});

test('unsubscribed skill edits are a no-op; subscribed edits affect only their destination', t => {
  const root = mkdtempSync(join(tmpdir(), 'skills-routing-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const folder of ['agents', 'skills']) cpSync(join(SOURCE_ROOT, folder), join(root, folder), { recursive: true });
  const before = Object.fromEntries(Object.entries(config).map(([name, target]) => [name, buildLibrary(root, target)]));
  const file = join(root, 'skills/laravel/actions/SKILL.md');
  writeFileSync(file, readFileSync(file, 'utf8') + '\nUpdated Laravel convention.\n');
  assert.deepEqual(buildLibrary(root, config['domain-driver']), before['domain-driver']);
  assert.notDeepEqual(buildLibrary(root, config.laracanon), before.laracanon);
  const updated = buildLibrary(root, config.laracanon);
  const nest = join(root, 'skills/nest/actions/SKILL.md');
  writeFileSync(nest, readFileSync(nest, 'utf8') + '\nUpdated Nest convention.\n');
  assert.deepEqual(buildLibrary(root, config.laracanon), updated);
  assert.notDeepEqual(buildLibrary(root, config['domain-driver']), before['domain-driver']);
});

test('snapshot updates remove retired files and legacy bundles, and preserve unrelated repo files', t => {
  const checkout = mkdtempSync(join(tmpdir(), 'skills-sync-'));
  t.after(() => rmSync(checkout, { recursive: true, force: true }));
  mkdirSync(join(checkout, '.git'));
  mkdirSync(join(checkout, 'factory'));
  writeFileSync(join(checkout, 'factory/old.md'), 'old bundle');
  writeFileSync(join(checkout, 'package.json'), '{"name":"consumer"}');
  syncLibrary(SOURCE_ROOT, config['domain-driver'], checkout);
  assert.ok(!existsSync(join(checkout, 'factory')));
  const retired = join(checkout, 'agent-library/skills/retired.md');
  writeFileSync(retired, 'retired');
  syncLibrary(SOURCE_ROOT, config['domain-driver'], checkout);
  assert.ok(!existsSync(retired));
  assert.equal(readFileSync(join(checkout, 'package.json'), 'utf8'), '{"name":"consumer"}');
});

test('an agent change reaches both destinations', t => {
  const root = mkdtempSync(join(tmpdir(), 'factory-routing-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  for (const folder of ['agents', 'skills']) cpSync(join(SOURCE_ROOT, folder), join(root, folder), { recursive: true });
  const before = Object.fromEntries(Object.entries(config).map(([name, target]) => [name, buildLibrary(root, target)]));
  const file = join(root, 'agents/factory/builder.md');
  writeFileSync(file, readFileSync(file, 'utf8') + '\nUpdated builder instruction.\n');
  for (const [name, target] of Object.entries(config)) {
    const updated = buildLibrary(root, target);
    assert.notDeepEqual(updated, before[name]);
    assert.match(updated.get('rendered/codex/builder.toml'), /Updated builder instruction/);
    assert.match(updated.get('rendered/claude/builder.md'), /Updated builder instruction/);
  }
});

test('a symlinked destination parent cannot redirect snapshot replacement outside the checkout', t => {
  const checkout = mkdtempSync(join(tmpdir(), 'skills-dest-'));
  const outside = mkdtempSync(join(tmpdir(), 'skills-outside-'));
  t.after(() => {
    rmSync(checkout, { recursive: true, force: true });
    rmSync(outside, { recursive: true, force: true });
  });
  mkdirSync(join(checkout, '.git'));
  writeFileSync(join(outside, 'mine.md'), 'mine');
  symlinkSync(outside, join(checkout, 'resources'));
  assert.throws(() => syncLibrary(SOURCE_ROOT, config.laracanon, checkout), /Symlinks/);
  assert.equal(readFileSync(join(outside, 'mine.md'), 'utf8'), 'mine');
});

test('refuses unmanaged output and source symlinks before deleting existing content', t => {
  const checkout = mkdtempSync(join(tmpdir(), 'skills-safe-'));
  t.after(() => rmSync(checkout, { recursive: true, force: true }));
  mkdirSync(join(checkout, '.git'));
  mkdirSync(join(checkout, 'agent-library'));
  writeFileSync(join(checkout, 'agent-library/mine.md'), 'mine');
  assert.throws(() => syncLibrary(SOURCE_ROOT, config['domain-driver'], checkout), /unmanaged directory/);
  assert.equal(readFileSync(join(checkout, 'agent-library/mine.md'), 'utf8'), 'mine');
  const root = join(checkout, 'source');
  cpSync(join(SOURCE_ROOT, 'skills'), join(root, 'skills'), { recursive: true });
  symlinkSync(join(checkout, 'package.json'), join(root, 'skills/laravel/actions/external.md'));
  assert.throws(() => syncLibrary(root, config.laracanon, checkout), /Symlinks/);
  assert.equal(readFileSync(join(checkout, 'agent-library/mine.md'), 'utf8'), 'mine');
});
