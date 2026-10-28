import { existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, isAbsolute, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

export const SOURCE_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const HOSTS = ['.ai/skills', '.agents/skills', '.claude/skills'];
const AGENT_FIELDS = ['name', 'description', 'claude-model', 'claude-tools', 'claude-effort', 'codex-model', 'codex-reasoning-effort'];

export function targets(root = SOURCE_ROOT) {
  return JSON.parse(readFileSync(join(root, 'distribution/targets.json'), 'utf8'));
}

function inside(root, file) {
  if (isAbsolute(file) || file.split(/[\\/]/).some(part => part === '..' || part === '.' || part === '')) {
    throw new Error(`Expected a relative file path: ${file}`);
  }
  const absolute = resolve(root, file);
  if (!absolute.startsWith(resolve(root) + sep)) throw new Error(`Path escapes its root: ${file}`);
  let candidate = resolve(root);
  for (const part of file.split('/')) {
    candidate = join(candidate, part);
    if (lstatSync(candidate, { throwIfNoEntry: false })?.isSymbolicLink()) throw new Error(`Symlinks are not distributed: ${file}`);
  }
  return absolute;
}

function filesUnder(root, prefix) {
  const directory = inside(root, prefix);
  if (lstatSync(directory).isSymbolicLink()) throw new Error(`Symlinks are not distributed: ${prefix}`);
  return readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap(entry => {
    const file = `${prefix}/${entry.name}`;
    if (entry.isSymbolicLink()) throw new Error(`Symlinks are not distributed: ${file}`);
    if (entry.isDirectory()) return filesUnder(root, file);
    if (!entry.isFile()) throw new Error(`Not a regular file: ${file}`);
    return [file];
  });
}

function field(text, key, label) {
  const header = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text)?.[1];
  const value = header?.split(/\r?\n/).find(line => line.startsWith(`${key}: `))?.slice(key.length + 2).trim();
  if (!value || /^[>|]/.test(value)) throw new Error(`${label}: expected a single-line ${key}`);
  if (value.startsWith('"')) return JSON.parse(value);
  if (value.startsWith("'")) return value.slice(1, -1).replaceAll("''", "'");
  return value;
}

function agentOutput(text, label) {
  const values = Object.fromEntries(AGENT_FIELDS.map(key => [key, field(text, key, label)]));
  const body = text.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n\r?\n?/, '');
  if (body.includes("'''")) throw new Error(`${label}: unsupported TOML literal delimiter`);
  return {
    name: values.name,
    claude: `---\nname: ${values.name}\ndescription: ${JSON.stringify(values.description)}\ntools: ${values['claude-tools']}\nmodel: ${values['claude-model']}\neffort: ${values['claude-effort']}\n---\n\n${body}`,
    codex: `name = ${JSON.stringify(values.name)}\ndescription = ${JSON.stringify(values.description)}\nmodel = ${JSON.stringify(values['codex-model'])}\nmodel_reasoning_effort = ${JSON.stringify(values['codex-reasoning-effort'])}\ndeveloper_instructions = '''\n${body}'''\n`,
  };
}

function catalog(skills) {
  const rows = skills.map(skill => `| ${skill.id} | \`${skill.id}/SKILL.md\` | ${skill.description.replaceAll('|', '\\|')} |`);
  return `# Installed skill catalog\n\nGenerated from IsaacHatilima/skills. Only the skills delivered to this consumer are listed.\n\n## Resolve skill files\n\nA skill id is its grouped source path. In project-native roots it uses a group-prefixed folder, such as \`laravel-actions/SKILL.md\`.\n\n1. Prefer a copy in the target worktree's \`.agents/skills/\`, \`.claude/skills/\`, or \`.ai/skills/\`.\n2. Then use the supplied library roots in their stated order: a grouped canonical path, or the group-prefixed folder in a flat root.\n\nRead the selected file and record its absolute path. Conflicting copies at the same priority require an explicit selection. Library roots outside the target worktree are read-only. Missing required skills block the relevant stage; missing unused groups do not. Project guidance takes precedence. Skills do not expand write ownership or authorize external effects.\n\n## Available skills\n\n| Skill id | Canonical path | Use when |\n|---|---|---|\n${rows.join('\n')}\n`;
}

/** Build a deterministic snapshot. No commit id is stored, so unrelated changes are a no-op. */
export function buildLibrary(root, target) {
  const output = new Map();
  const items = [];
  const skillMetadata = [];
  const groups = readdirSync(join(root, 'skills'), { withFileTypes: true })
    .filter(entry => entry.isDirectory() && (target.groups.includes('*') || target.groups.includes(entry.name)) && !target.excludeGroups.includes(entry.name))
    .map(entry => entry.name).sort();
  for (const group of target.groups.filter(group => group !== '*')) {
    if (!groups.includes(group)) throw new Error(`Required skill group is missing: ${group}`);
  }
  const add = (file, text) => {
    inside(root, file);
    if (output.has(file)) throw new Error(`Duplicate output: ${file}`);
    output.set(file, text);
  };
  for (const group of groups) {
    const skills = readdirSync(join(root, 'skills', group), { withFileTypes: true }).filter(entry => entry.isDirectory()).map(entry => entry.name).sort();
    for (const name of skills) {
      const id = `${group}/${name}`;
      const prefix = `skills/${id}`;
      const text = readFileSync(join(root, prefix, 'SKILL.md'), 'utf8');
      if (field(text, 'name', `${id}/SKILL.md`) !== name) throw new Error(`${id}: name does not match its source folder`);
      const description = field(text, 'description', `${id}/SKILL.md`);
      const nativeName = `${group}-${name}`;
      const paths = {};
      for (const file of filesUnder(root, prefix)) {
        const suffix = file.slice(prefix.length + 1);
        let contents = readFileSync(join(root, file), 'utf8');
        if (suffix === 'SKILL.md') {
          contents = contents.replace(/^name: [^\r\n]+/m, `name: ${nativeName}`)
            .replace(/^description: [^\r\n]+/m, `description: ${JSON.stringify(description)}`);
        }
        add(file, contents);
        for (const host of HOSTS) paths[`${host}/${nativeName}/${suffix}`] = file;
      }
      items.push({ name: nativeName, description, files: paths });
      skillMetadata.push({ id, description });
    }
  }
  add('skills/catalog.md', catalog(skillMetadata));
  for (const name of target.agents) {
    const prefix = `agents/${name}`;
    const paths = {};
    const text = readFileSync(join(root, prefix, 'SKILL.md'), 'utf8');
    for (const file of filesUnder(root, prefix)) {
      add(file, readFileSync(join(root, file), 'utf8'));
      const suffix = file.slice(prefix.length + 1);
      for (const host of HOSTS) paths[`${host}/${name}/${suffix}`] = file;
      if (file.endsWith('.md') && !['AGENT.md', 'SKILL.md', 'README.md'].includes(suffix) && !suffix.includes('/')) {
        const agent = agentOutput(output.get(file), file);
        if (suffix !== `${agent.name}.md`) throw new Error(`${file}: name does not match filename`);
        for (const [host, extension] of [['claude', 'md'], ['codex', 'toml']]) {
          const rendered = `rendered/${host}/${agent.name}.${extension}`;
          add(rendered, agent[host]);
          paths[`.${host}/agents/${agent.name}.${extension}`] = rendered;
        }
      }
    }
    for (const host of HOSTS) paths[`${host}/catalog.md`] = 'skills/catalog.md';
    items.push({ name, description: field(text, 'description', `${prefix}/SKILL.md`), files: paths });
  }
  items.sort((a, b) => a.name.localeCompare(b.name));
  if (new Set(items.map(item => item.name)).size !== items.length) throw new Error('Duplicate native skill or workflow name');
  add('catalog.json', `${JSON.stringify({ schema: 1, source: 'https://github.com/IsaacHatilima/skills', items }, null, 2)}\n`);
  add('README.md', '# Generated agent library\n\nManaged by [IsaacHatilima/skills](https://github.com/IsaacHatilima/skills). Edit skills and factory agents there; its main-branch workflow opens update PRs here.\n\n`catalog.json` maps each installable item to its project files. `agents/` and `skills/` preserve the shared layout; `rendered/` contains host-specific child agents.\n');
  return output;
}

export function syncLibrary(root, target, checkout) {
  if (!existsSync(join(checkout, '.git'))) throw new Error('Destination must be a git checkout');
  const output = buildLibrary(root, target);
  const destination = inside(checkout, target.directory);
  const legacyDirectories = target.legacyDirectories.map(legacy => inside(checkout, legacy));
  if (existsSync(destination) && !existsSync(join(destination, 'catalog.json'))) throw new Error(`Refusing to replace an unmanaged directory: ${destination}`);
  if (existsSync(destination) && lstatSync(destination).isSymbolicLink()) throw new Error('Destination cannot be a symlink');
  // Build everything before removing any managed content.
  rmSync(destination, { recursive: true, force: true });
  for (const [file, contents] of output) {
    const absolute = inside(destination, file);
    mkdirSync(dirname(absolute), { recursive: true });
    writeFileSync(absolute, contents);
  }
  for (const legacy of legacyDirectories) rmSync(legacy, { recursive: true, force: true });
  return output.size;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [name, checkout] = process.argv.slice(2);
  const config = targets();
  if (name === '--matrix') {
    console.log(JSON.stringify({ include: Object.entries(config).map(([target, value]) => ({ target, ...value })) }));
  } else {
    if (!config[name] || !checkout) throw new Error('Usage: node scripts/sync-skills.mjs <laracanon|domain-driver> <checkout>');
    console.log(`Synced ${syncLibrary(SOURCE_ROOT, config[name], resolve(checkout))} files to ${name}.`);
  }
}
