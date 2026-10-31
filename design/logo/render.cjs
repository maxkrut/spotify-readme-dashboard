/* Use Sharp from an existing external runtime, for example through NODE_PATH. */
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');

async function main() {
  const root = __dirname;
  const set = process.argv[2] || '1';
  if (!['1', '2', '3', '4', 'all'].includes(set)) throw new Error('Expected proposal set 1, 2, 3, 4 or all.');
  const suffix = set === 'all' ? '-all' : (set === '1' ? '' : `-${set.padStart(2, '0')}`);
  const config = JSON.parse(fs.readFileSync(path.join(root, `variants${suffix}.json`), 'utf8'));
  const filenames = new Set(config.variants.flatMap(v => Object.keys(config.themes).map(t => `${v.id}-${t}.svg`)));
  const svg = fs.readFileSync(path.join(root, `comparison${suffix}.svg`));
  await sharp(svg, { density: 144 }).png().toFile(path.join(root, `comparison${suffix}@2x.png`));
  const dir = path.join(root, 'exports');
  const names = fs.readdirSync(dir).filter(n => filenames.has(n));
  for (const name of names) {
    await sharp(fs.readFileSync(path.join(dir, name)), { density: 288 })
      .png().toFile(path.join(dir, name.replace('.svg', '@4x.png')));
  }
  console.log(`Saved set ${set} comparison at 2x and ${names.length} transparent logo PNGs at 4x.`);
}

main().catch(error => { console.error(error); process.exitCode = 1; });
