//! Spike (c): harness do formato .rbsc (SQLite WAL). Experimento descartável; nunca vai para produção.
//!
//! Subcomandos:
//!   fill <db> [normal|full] [dense] cria um arquivo com R-A (4096x4096, 30 camadas RGBA8); dense = todas as camadas 100% preenchidas
//!   open <db>                      mede a abertura progressiva
//!   compress                       zstd vs lz4 em tiles 256x256 RGBA8
//!   crash-run <dir> <n> <normal|full> [reset_every]   n interrupções forçadas durante escrita
//!   worker <db> <normal|full>      (interno) escreve transações até ser morto
use rusqlite::{params, Connection};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

const SCHEMA: &str = include_str!("../../../../contracts/document-format/rbsc-schema-v1.sql");
const TS: usize = 256;
const TILE_BYTES: usize = TS * TS * 4;
const GRID: usize = 16; // 4096 / 256
const LAYERS: usize = 30;

type R<T> = Result<T, Box<dyn std::error::Error>>;

// ----------------------------------------------------------------------------- RNG
struct Rng(u64);
impl Rng {
    fn new(seed: u64) -> Self {
        Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1)
    }
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 >> 12;
        self.0 ^= self.0 << 25;
        self.0 ^= self.0 >> 27;
        self.0.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn f(&mut self) -> f32 {
        (self.next() >> 40) as f32 / (1u64 << 24) as f32
    }
    fn range(&mut self, lo: u64, hi: u64) -> u64 {
        lo + self.next() % (hi - lo)
    }
}
fn seed_now() -> u64 {
    SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos() as u64 ^ (std::process::id() as u64) << 32
}

// ----------------------------------------------------------------------------- tiles sintéticos
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Kind {
    Flat,
    Background, // gradiente suave + granulação leve, opaco
    Painted,    // pinceladas macias sobre transparente
    Grain,      // pinceladas + granulação de papel
    Random,     // pior caso: ruído puro
}

fn gen_tile(kind: Kind, rng: &mut Rng) -> Vec<u8> {
    let mut px = vec![0u8; TILE_BYTES];
    match kind {
        Kind::Flat => {
            let c = [rng.range(0, 256) as u8, rng.range(0, 256) as u8, rng.range(0, 256) as u8, 255];
            for p in px.chunks_exact_mut(4) {
                p.copy_from_slice(&c);
            }
        }
        Kind::Background => {
            let (r0, g0, b0) = (rng.f() * 200.0, rng.f() * 200.0, rng.f() * 200.0);
            let (dx, dy) = (rng.f() * 0.25, rng.f() * 0.25);
            for y in 0..TS {
                for x in 0..TS {
                    let i = (y * TS + x) * 4;
                    let t = x as f32 * dx + y as f32 * dy;
                    let n = (rng.next() % 7) as f32 - 3.0;
                    px[i] = (r0 + t + n).clamp(0.0, 255.0) as u8;
                    px[i + 1] = (g0 + t * 0.8 + n).clamp(0.0, 255.0) as u8;
                    px[i + 2] = (b0 + t * 0.6 + n).clamp(0.0, 255.0) as u8;
                    px[i + 3] = 255;
                }
            }
        }
        Kind::Painted | Kind::Grain => {
            let strokes = rng.range(3, 9);
            for _ in 0..strokes {
                let (x0, y0) = (rng.f() * TS as f32, rng.f() * TS as f32);
                let (x1, y1) = (rng.f() * TS as f32, rng.f() * TS as f32);
                let radius = 6.0 + rng.f() * 24.0;
                let col = [rng.f() * 255.0, rng.f() * 255.0, rng.f() * 255.0];
                let len = ((x1 - x0).powi(2) + (y1 - y0).powi(2)).sqrt().max(1.0);
                let steps = (len / 2.0) as usize + 1;
                for s in 0..steps {
                    let t = s as f32 / steps as f32;
                    let (cx, cy) = (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t);
                    let (ylo, yhi) = ((cy - radius).max(0.0) as usize, ((cy + radius) as usize).min(TS - 1));
                    let (xlo, xhi) = ((cx - radius).max(0.0) as usize, ((cx + radius) as usize).min(TS - 1));
                    for y in ylo..=yhi {
                        for x in xlo..=xhi {
                            let d = ((x as f32 - cx).powi(2) + (y as f32 - cy).powi(2)).sqrt();
                            if d >= radius {
                                continue;
                            }
                            let a = (1.0 - d / radius).powi(2) * 0.35;
                            let i = (y * TS + x) * 4;
                            let da = px[i + 3] as f32 / 255.0;
                            let oa = a + da * (1.0 - a);
                            for k in 0..3 {
                                let dc = px[i + k] as f32;
                                px[i + k] = ((col[k] * a + dc * da * (1.0 - a)) / oa).clamp(0.0, 255.0) as u8;
                            }
                            px[i + 3] = (oa * 255.0) as u8;
                        }
                    }
                }
            }
            if kind == Kind::Grain {
                for p in px.chunks_exact_mut(4) {
                    if p[3] > 0 {
                        let n = (rng.next() % 11) as i32 - 5;
                        for k in 0..3 {
                            p[k] = (p[k] as i32 + n).clamp(0, 255) as u8;
                        }
                    }
                }
            }
        }
        Kind::Random => {
            for chunk in px.chunks_exact_mut(8) {
                chunk.copy_from_slice(&rng.next().to_le_bytes());
            }
        }
    }
    px
}

// ----------------------------------------------------------------------------- banco
fn open_conn(path: &Path, sync: &str) -> R<Connection> {
    let conn = Connection::open(path)?;
    conn.busy_timeout(Duration::from_secs(5))?;
    let mode: String = conn.query_row("PRAGMA journal_mode=WAL", [], |r| r.get(0))?;
    assert_eq!(mode.to_lowercase(), "wal");
    conn.execute_batch(&format!("PRAGMA foreign_keys=ON; PRAGMA synchronous={};", sync.to_uppercase()))?;
    Ok(conn)
}

fn uuid(n: u64) -> Vec<u8> {
    let mut v = vec![0u8; 16];
    v[8..].copy_from_slice(&n.to_be_bytes());
    v[6] = 0x70;
    v
}

fn init_db(path: &Path, sync: &str) -> R<Connection> {
    for suffix in ["", "-wal", "-shm"] {
        let _ = std::fs::remove_file(format!("{}{}", path.display(), suffix));
    }
    let conn = open_conn(path, sync)?;
    conn.execute_batch(SCHEMA)?;
    Ok(conn)
}

fn insert_nodes(conn: &Connection, layers: usize) -> R<()> {
    conn.execute(
        "INSERT INTO nodes(node_id,parent_id,kind,ord,name,transform) VALUES(?,NULL,'Document','a0','doc',?)",
        params![uuid(1), vec![0u8; 24]],
    )?;
    for l in 0..layers {
        conn.execute(
            "INSERT INTO nodes(node_id,parent_id,kind,ord,name,transform) VALUES(?,?,'RasterLayer',?,?,?)",
            params![uuid(100 + l as u64), uuid(1), format!("a{:03}", l + 1), format!("camada {}", l), vec![0u8; 24]],
        )?;
    }
    conn.execute(
        "INSERT INTO document_meta(doc_id,width,height,dpi,color_profile,bit_depth,blend_space) VALUES(?,4096,4096,300,?,8,'perceptual')",
        params![uuid(1), vec![0u8; 3144]],
    )?;
    for (k, v) in [("schema_version", "1.0.0"), ("created_at", "2026-11-25"), ("last_modified", "2026-11-25"), ("app_version", "spike-c"), ("doc_id", "spike")] {
        conn.execute("INSERT INTO file_meta(key,value) VALUES(?,?)", params![k, v])?;
    }
    Ok(())
}

// ----------------------------------------------------------------------------- fill
fn cmd_fill(db: &Path, sync: &str, dense: bool) -> R<()> {
    let t0 = Instant::now();
    let mut conn = init_db(db, sync)?;
    let tx = conn.transaction()?;
    insert_nodes(&tx, LAYERS)?;
    let mut rng = Rng::new(42);
    let (mut raw, mut stored, mut n_tiles, mut n_refs) = (0usize, 0usize, 0usize, 0usize);
    {
        let mut ins_tile = tx.prepare("INSERT OR IGNORE INTO tiles(hash,codec,raw_len,data) VALUES(?,'zstd',?,?)")?;
        let mut ins_ref = tx.prepare("INSERT INTO tile_refs(layer_id,mip,col,row,tile_hash) VALUES(?,0,?,?,?)")?;
        for l in 0..LAYERS {
            let coverage = if l == 0 || dense { 1.0 } else { 0.35 + (l % 5) as f32 * 0.1 };
            let flat_color_tile = gen_tile(Kind::Flat, &mut rng);
            for row in 0..GRID {
                for col in 0..GRID {
                    if rng.f() > coverage {
                        continue; // tile vazio: sem referência
                    }
                    let kind = if l == 0 {
                        Kind::Background
                    } else if rng.f() < 0.05 {
                        Kind::Flat
                    } else if l % 2 == 0 {
                        Kind::Painted
                    } else {
                        Kind::Grain
                    };
                    let px = if kind == Kind::Flat { flat_color_tile.clone() } else { gen_tile(kind, &mut rng) };
                    let h = blake3::hash(&px);
                    let z = zstd::bulk::compress(&px, 3)?;
                    raw += px.len();
                    let changed = ins_tile.execute(params![h.as_bytes().to_vec(), px.len() as i64, z.clone()])?;
                    if changed > 0 {
                        stored += z.len();
                        n_tiles += 1;
                    }
                    ins_ref.execute(params![uuid(100 + l as u64), col as i64, row as i64, h.as_bytes().to_vec()])?;
                    n_refs += 1;
                }
            }
        }
    }
    tx.commit()?;
    conn.execute_batch("PRAGMA wal_checkpoint(TRUNCATE);")?;
    let size = std::fs::metadata(db)?.len();
    println!("fill: {:.1}s | tile_refs={} tiles_unicos={} (dedup {}) | bruto={:.0} MiB comprimido(zstd3)={:.0} MiB | arquivo={:.0} MiB",
        t0.elapsed().as_secs_f64(), n_refs, n_tiles, n_refs - n_tiles, raw as f64 / 1048576.0, stored as f64 / 1048576.0, size as f64 / 1048576.0);
    Ok(())
}

// ----------------------------------------------------------------------------- open
fn ms(d: Duration) -> f64 {
    d.as_secs_f64() * 1000.0
}

fn cmd_open(db: &Path) -> R<()> {
    let t0 = Instant::now();
    let conn = open_conn(db, "normal")?;
    let t_conn = t0.elapsed();
    // Fase 1: árvore (document_meta, nodes, tile_refs)
    let _w: i64 = conn.query_row("SELECT width FROM document_meta", [], |r| r.get(0))?;
    let nodes: i64 = conn.query_row("SELECT count(*) FROM nodes", [], |r| r.get(0))?;
    let mut refs = Vec::new();
    {
        let mut st = conn.prepare("SELECT layer_id,col,row,tile_hash FROM tile_refs")?;
        let rows = st.query_map([], |r| Ok((r.get::<_, Vec<u8>>(0)?, r.get::<_, i64>(1)?, r.get::<_, i64>(2)?, r.get::<_, Vec<u8>>(3)?)))?;
        for r in rows {
            refs.push(r?);
        }
    }
    let t_tree = t0.elapsed();
    // Fase 2: tiles do viewport (<= 50 tiles, região 8x6 do canto, camadas de cima para baixo)
    let mut wanted: Vec<&Vec<u8>> = refs.iter().filter(|r| r.1 < 8 && r.2 < 7).map(|r| &r.3).collect();
    wanted.dedup();
    wanted.truncate(50);
    let mut st = conn.prepare("SELECT raw_len,data FROM tiles WHERE hash=?")?;
    let mut bytes = 0usize;
    for h in &wanted {
        let (raw_len, data): (i64, Vec<u8>) = st.query_row(params![h], |r| Ok((r.get(0)?, r.get(1)?)))?;
        let px = zstd::bulk::decompress(&data, raw_len as usize)?;
        bytes += px.len();
    }
    let t_view = t0.elapsed();
    // Fase 3: o resto em "segundo plano" (aqui, sequencial; mede o custo total)
    let all: Vec<Vec<u8>> = {
        let mut s = conn.prepare("SELECT hash FROM tiles")?;
        let rows = s.query_map([], |r| r.get::<_, Vec<u8>>(0))?;
        rows.collect::<Result<_, _>>()?
    };
    let t_bg0 = Instant::now();
    for h in &all {
        let (raw_len, data): (i64, Vec<u8>) = st.query_row(params![h], |r| Ok((r.get(0)?, r.get(1)?)))?;
        let _ = zstd::bulk::decompress(&data, raw_len as usize)?;
    }
    let t_bg = t_bg0.elapsed();
    let t1 = Instant::now();
    let q: String = conn.query_row("PRAGMA quick_check", [], |r| r.get(0))?;
    let t_quick = t1.elapsed();
    let t2 = Instant::now();
    let i: String = conn.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
    let t_int = t2.elapsed();
    println!(
        "open: conexao={:.0} ms | arvore pronta={:.0} ms ({} nos, {} refs) | viewport pronto={:.0} ms ({} tiles, {:.1} MiB) | resto em segundo plano={:.0} ms ({} tiles) | quick_check={:.0} ms ({}) | integrity_check={:.0} ms ({})",
        ms(t_conn), ms(t_tree), nodes, refs.len(), ms(t_view), wanted.len(), bytes as f64 / 1048576.0, ms(t_bg), all.len(), ms(t_quick), q, ms(t_int), i
    );
    Ok(())
}

// ----------------------------------------------------------------------------- compress
fn pct(v: &mut Vec<f64>, p: f64) -> f64 {
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[((v.len() as f64 * p) as usize).min(v.len() - 1)]
}

fn cmd_compress() -> R<()> {
    let classes = [("plano", Kind::Flat), ("fundo", Kind::Background), ("pinceladas", Kind::Painted), ("pinceladas+grao", Kind::Grain), ("ruido(pior caso)", Kind::Random)];
    println!("classe | codec | tamanho medio | razao | compress p50/p95/max (ms) | decompress p50/p95 (ms)");
    for (name, kind) in classes {
        let mut rng = Rng::new(7);
        let tiles: Vec<Vec<u8>> = (0..300).map(|_| gen_tile(kind, &mut rng)).collect();
        let raw: usize = tiles.iter().map(|t| t.len()).sum();
        let configs: Vec<(&str, Box<dyn Fn(&[u8]) -> Vec<u8>>, Box<dyn Fn(&[u8]) -> Vec<u8>>)> = vec![
            ("zstd-1", Box::new(|d| zstd::bulk::compress(d, 1).unwrap()), Box::new(|c| zstd::bulk::decompress(c, TILE_BYTES).unwrap())),
            ("zstd-3", Box::new(|d| zstd::bulk::compress(d, 3).unwrap()), Box::new(|c| zstd::bulk::decompress(c, TILE_BYTES).unwrap())),
            ("zstd-9", Box::new(|d| zstd::bulk::compress(d, 9).unwrap()), Box::new(|c| zstd::bulk::decompress(c, TILE_BYTES).unwrap())),
            ("lz4", Box::new(|d| lz4_flex::block::compress(d)), Box::new(|c| lz4_flex::block::decompress(c, TILE_BYTES).unwrap())),
        ];
        for (cname, comp, decomp) in &configs {
            let (mut tc, mut td, mut size) = (Vec::new(), Vec::new(), 0usize);
            for t in &tiles {
                let a = Instant::now();
                let c = comp(t);
                tc.push(ms(a.elapsed()));
                size += c.len();
                let b = Instant::now();
                let d = decomp(&c);
                td.push(ms(b.elapsed()));
                assert_eq!(d.len(), t.len());
            }
            let max = tc.iter().cloned().fold(0.0, f64::max);
            println!("{} | {} | {:.1} KiB | {:.2}x | {:.2} / {:.2} / {:.2} | {:.2} / {:.2}", name, cname, size as f64 / tiles.len() as f64 / 1024.0,
                raw as f64 / size as f64, pct(&mut tc, 0.5), pct(&mut tc, 0.95), max, pct(&mut td, 0.5), pct(&mut td, 0.95));
        }
    }
    Ok(())
}

// ----------------------------------------------------------------------------- crash
fn cmd_worker(db: &Path, sync: &str) -> R<()> {
    let mut conn = open_conn(db, sync)?;
    let mut rng = Rng::new(seed_now());
    loop {
        let tx = conn.transaction()?;
        let mut hashes = Vec::new();
        for _ in 0..2 {
            let kind = if rng.f() < 0.5 { Kind::Painted } else { Kind::Grain };
            let px = gen_tile(kind, &mut rng);
            let h = blake3::hash(&px);
            let z = zstd::bulk::compress(&px, 3)?;
            tx.execute("INSERT OR IGNORE INTO tiles(hash,codec,raw_len,data) VALUES(?,'zstd',?,?)", params![h.as_bytes().to_vec(), px.len() as i64, z])?;
            tx.execute(
                "INSERT OR REPLACE INTO tile_refs(layer_id,mip,col,row,tile_hash) VALUES(?,0,?,?,?)",
                params![uuid(100), rng.range(0, GRID as u64) as i64, rng.range(0, GRID as u64) as i64, h.as_bytes().to_vec()],
            )?;
            hashes.push(h.to_hex().to_string());
        }
        let payload = zstd::bulk::compress(format!("{{\"tiles\":{:?}}}", hashes).as_bytes(), 3)?;
        let op_id = rng.next().to_be_bytes().iter().chain(rng.next().to_be_bytes().iter()).cloned().collect::<Vec<u8>>();
        tx.execute(
            "INSERT INTO oplog(op_id,author_id,device_id,hlc_ts,hlc_counter,base_seq,schema_version,op_type,targets,payload,inverse) VALUES(?,?,?,0,0,0,'1.0.0','Stroke',x'5b5d',?,?)",
            params![op_id, uuid(7), uuid(8), payload.clone(), payload],
        )?;
        let seq = tx.last_insert_rowid();
        tx.execute("UPDATE nodes SET extra=? WHERE node_id=?", params![seq.to_string().into_bytes(), uuid(100)])?;
        tx.commit()?;
    }
}

#[derive(Default)]
struct Verdict {
    ok: bool,
    problems: Vec<String>,
    wal_bytes: u64,
    ops: i64,
}

fn verify(db: &Path) -> R<Verdict> {
    let mut v = Verdict { ok: true, ..Default::default() };
    v.wal_bytes = std::fs::metadata(format!("{}-wal", db.display())).map(|m| m.len()).unwrap_or(0);
    let conn = open_conn(db, "normal")?;
    let ic: String = conn.query_row("PRAGMA integrity_check", [], |r| r.get(0))?;
    if ic != "ok" {
        v.problems.push(format!("integrity_check: {}", ic));
    }
    let fk: i64 = conn.query_row("SELECT count(*) FROM pragma_foreign_key_check", [], |r| r.get(0))?;
    if fk != 0 {
        v.problems.push(format!("foreign_key_check: {} violações", fk));
    }
    let (count, max): (i64, Option<i64>) = conn.query_row("SELECT count(*), max(seq) FROM oplog", [], |r| Ok((r.get(0)?, r.get(1)?)))?;
    v.ops = count;
    if count != max.unwrap_or(0) {
        v.problems.push(format!("oplog com buraco: count={} max(seq)={:?}", count, max));
    }
    let extra: Option<Vec<u8>> = conn.query_row("SELECT extra FROM nodes WHERE node_id=?", params![uuid(100)], |r| r.get(0))?;
    let last_seq: i64 = extra.and_then(|b| String::from_utf8(b).ok()).and_then(|s| s.parse().ok()).unwrap_or(0);
    if last_seq != max.unwrap_or(0) {
        v.problems.push(format!("estado materializado fora do oplog: nodes.extra={} max(seq)={:?}", last_seq, max));
    }
    // últimas operações: o payload cita tiles que precisam existir e bater com o hash
    let mut st = conn.prepare("SELECT payload FROM oplog ORDER BY seq DESC LIMIT 20")?;
    let payloads: Vec<Vec<u8>> = st.query_map([], |r| r.get(0))?.collect::<Result<_, _>>()?;
    for p in payloads {
        let json = String::from_utf8(zstd::bulk::decompress(&p, 1 << 16)?)?;
        for h in json.split('"').filter(|s| s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())) {
            let bytes: Vec<u8> = (0..32).map(|i| u8::from_str_radix(&h[2 * i..2 * i + 2], 16).unwrap()).collect();
            match conn.query_row("SELECT raw_len,data FROM tiles WHERE hash=?", params![bytes], |r| Ok((r.get::<_, i64>(0)?, r.get::<_, Vec<u8>>(1)?))) {
                Ok((raw_len, data)) => {
                    let px = zstd::bulk::decompress(&data, raw_len as usize)?;
                    if blake3::hash(&px).to_hex().to_string() != h {
                        v.problems.push(format!("tile {} com conteúdo corrompido", h));
                    }
                }
                Err(_) => v.problems.push(format!("tile {} citado no oplog não existe", h)),
            }
        }
    }
    v.ok = v.problems.is_empty();
    Ok(v)
}

fn cmd_crash_run(dir: &Path, n: usize, sync: &str, reset_every: usize) -> R<()> {
    std::fs::create_dir_all(dir)?;
    let db: PathBuf = dir.join(format!("crash-{}.rbsc", sync));
    let exe = std::env::current_exe()?;
    let mut rng = Rng::new(seed_now());
    let (mut corrupt, mut with_wal, mut total_ops_seen) = (0usize, 0usize, 0i64);
    let _ = &mut total_ops_seen;
    let t0 = Instant::now();
    for i in 0..n {
        if i % reset_every == 0 {
            let c = init_db(&db, sync)?;
            insert_nodes(&c, 1)?;
            drop(c);
        }
        let mut child = Command::new(&exe).arg("worker").arg(&db).arg(sync).stdout(Stdio::null()).stderr(Stdio::null()).spawn()?;
        std::thread::sleep(Duration::from_millis(rng.range(30, 500)));
        child.kill()?; // TerminateProcess no Windows (equivalente ao kill -9: sem flush, sem handlers)
        child.wait()?;
        let v = verify(&db)?;
        if v.wal_bytes > 0 {
            with_wal += 1;
        }
        total_ops_seen = v.ops;
        if !v.ok {
            corrupt += 1;
            println!("[{}] FALHA: {:?}", i + 1, v.problems);
        }
        if (i + 1) % 50 == 0 {
            println!("[{}/{}] corrupcoes={} reabertura_com_WAL_pendente={} oplog_atual={} ({:.0}s)", i + 1, n, corrupt, with_wal, total_ops_seen, t0.elapsed().as_secs_f64());
        }
    }
    println!("RESULTADO sync={} interrupcoes={} corrupcoes={} reaberturas_com_WAL_pendente={} tempo={:.0}s", sync, n, corrupt, with_wal, t0.elapsed().as_secs_f64());
    Ok(())
}

fn main() -> R<()> {
    let a: Vec<String> = std::env::args().collect();
    let arg = |i: usize| a.get(i).map(|s| s.as_str());
    match arg(1) {
        Some("fill") => cmd_fill(Path::new(arg(2).ok_or("db")?), arg(3).unwrap_or("normal"), arg(4) == Some("dense")),
        Some("open") => cmd_open(Path::new(arg(2).ok_or("db")?)),
        Some("compress") => cmd_compress(),
        Some("worker") => cmd_worker(Path::new(arg(2).ok_or("db")?), arg(3).unwrap_or("normal")),
        Some("crash-run") => cmd_crash_run(Path::new(arg(2).ok_or("dir")?), arg(3).ok_or("n")?.parse()?, arg(4).unwrap_or("normal"), arg(5).map(|s| s.parse().unwrap()).unwrap_or(50)),
        _ => {
            eprintln!("uso: fill|open|compress|crash-run|worker (veja o cabeçalho de main.rs)");
            std::process::exit(2);
        }
    }
}
