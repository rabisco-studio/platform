// Spike (c): SQLite em WASM com OPFS. Roda dentro de um Worker (o VFS OPFS só existe fora da thread principal).
import sqlite3InitModule from './node_modules/@sqlite.org/sqlite-wasm/dist/index.mjs';

const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');

// Tile sintético semi-compressível (~64 KiB, determinístico por índice)
function tile(i) {
  const a = new Uint8Array(65536);
  let x = (i + 1) * 2654435761 >>> 0;
  for (let k = 0; k < a.length; k++) {
    if (k % 64 < 40) { a[k] = (k >> 6) & 255; } else { x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0; a[k] = x & 255; }
  }
  return a;
}

self.onmessage = async (e) => {
  const { phase, vfs, ddl, n } = e.data;
  const out = { phase, vfs };
  try {
    const sqlite3 = await sqlite3InitModule();
    out.sqlite = sqlite3.version.libVersion;
    out.crossOriginIsolated = self.crossOriginIsolated;
    out.sharedArrayBuffer = typeof SharedArrayBuffer !== 'undefined';
    let db;
    if (vfs === 'opfs') {
      out.opfsVfsAvailable = !!sqlite3.opfs;
      db = new sqlite3.oo1.OpfsDb('/spike-c-opfs.rbsc', 'c');
    } else {
      const pool = await sqlite3.installOpfsSAHPoolVfs({ name: 'spike-c-sah', directory: '/spike-c-sah', clearOnInit: false, initialCapacity: 6 });
      out.sahCapacity = pool.getCapacity();
      db = new pool.OpfsSAHPoolDb('/spike-c-sah.rbsc');
    }
    out.journalMode = db.selectValue('PRAGMA journal_mode=WAL');
    db.exec('PRAGMA foreign_keys=ON; PRAGMA synchronous=NORMAL;');
    if (phase === 'write') {
      const has = db.selectValue("SELECT count(*) FROM sqlite_master WHERE name='tiles'");
      if (!has) db.exec(ddl);
      const t0 = performance.now();
      db.exec('BEGIN');
      const ins = db.prepare('INSERT OR REPLACE INTO tiles(hash,codec,raw_len,data) VALUES(?,?,?,?)');
      for (let i = 0; i < n; i++) {
        const t = tile(i);
        const h = new Uint8Array(await crypto.subtle.digest('SHA-256', t));
        ins.bind([h, 'raw', t.length, t]).stepReset();
      }
      ins.finalize();
      db.exec('COMMIT');
      out.writeMs = Math.round(performance.now() - t0);
      out.tilesWritten = n;
      out.mibWritten = +((n * 65536) / 1048576).toFixed(1);
    } else {
      const t0 = performance.now();
      out.tilesFound = db.selectValue('SELECT count(*) FROM tiles');
      let bad = 0;
      const rows = db.selectArrays('SELECT hash,data FROM tiles');
      for (const [h, d] of rows) {
        const h2 = new Uint8Array(await crypto.subtle.digest('SHA-256', d));
        if (hex(h2) !== hex(h)) bad++;
      }
      out.readMs = Math.round(performance.now() - t0);
      out.hashMismatches = bad;
      out.integrity = db.selectValue('PRAGMA integrity_check');
    }
    out.finalJournalMode = db.selectValue('PRAGMA journal_mode');
    db.close();
    out.ok = true;
  } catch (err) {
    out.ok = false;
    out.error = String(err && err.message || err);
  }
  self.postMessage(out);
};
