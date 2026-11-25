//! Spike (d): pipeline de cor e 16 bits. Experimento descartável; nunca vai para produção.
//!
//! Subcomandos: ac1 | ac2 | ac4 | mem | compose | deltae-selftest
use moxcms::{ColorProfile, Layout, RenderingIntent, TransformOptions};
use rusqlite::{params, Connection};
use std::io::Cursor;
use std::time::Instant;

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
    fn f(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
}

// ----------------------------------------------------------------------------- matemática de cor (referência em f64)
fn srgb_decode(c: f64) -> f64 {
    if c <= 0.04045 { c / 12.92 } else { ((c + 0.055) / 1.055).powf(2.4) }
}
fn srgb_encode(c: f64) -> f64 {
    if c <= 0.0031308 { c * 12.92 } else { 1.055 * c.powf(1.0 / 2.4) - 0.055 }
}
const P3_TO_XYZ: [[f64; 3]; 3] = [
    [0.4865709486482162, 0.26566769316909306, 0.1982172852343625],
    [0.2289745640697488, 0.6917385218365064, 0.079286914093745],
    [0.0, 0.04511338185890264, 1.043944368900976],
];
const SRGB_TO_XYZ: [[f64; 3]; 3] = [
    [0.4123907992659595, 0.357584339383878, 0.1804807884018343],
    [0.21263900587151027, 0.715168678767756, 0.07219231536073371],
    [0.01933081871559182, 0.11919477979462598, 0.9505321522496607],
];
const XYZ_TO_SRGB: [[f64; 3]; 3] = [
    [3.2409699419045226, -1.537383177570094, -0.4986107602930034],
    [-0.9692436362808796, 1.8759675015077202, 0.04155505740717559],
    [0.05563007969699366, -0.20397695888897652, 1.0569715142428786],
];
fn mul(m: &[[f64; 3]; 3], v: [f64; 3]) -> [f64; 3] {
    [m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2], m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2], m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2]]
}
/// P3 codificado (0..1) -> sRGB codificado SEM recorte (pode sair de [0,1]).
fn p3_to_srgb_exact(p3: [f64; 3]) -> [f64; 3] {
    let lin = [srgb_decode(p3[0]), srgb_decode(p3[1]), srgb_decode(p3[2])];
    let l = mul(&XYZ_TO_SRGB, mul(&P3_TO_XYZ, lin));
    // codificação estendida (simétrica) para valores fora de [0,1]
    let enc = |x: f64| if x < 0.0 { -srgb_encode(-x) } else { srgb_encode(x) };
    [enc(l[0]), enc(l[1]), enc(l[2])]
}
fn srgb_to_lab(rgb: [f64; 3]) -> [f64; 3] {
    let dec = |x: f64| if x < 0.0 { -srgb_decode(-x) } else { srgb_decode(x) };
    let xyz = mul(&SRGB_TO_XYZ, [dec(rgb[0]), dec(rgb[1]), dec(rgb[2])]);
    let (xn, yn, zn) = (0.95047, 1.0, 1.08883);
    let f = |t: f64| if t > 216.0 / 24389.0 { t.cbrt() } else { (24389.0 / 27.0 * t + 16.0) / 116.0 };
    let (fx, fy, fz) = (f(xyz[0] / xn), f(xyz[1] / yn), f(xyz[2] / zn));
    [116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)]
}
/// ΔE 2000 (Sharma, Wu, Dalal 2005).
fn delta_e00(l1: [f64; 3], l2: [f64; 3]) -> f64 {
    let (pi, rad) = (std::f64::consts::PI, std::f64::consts::PI / 180.0);
    let (c1, c2) = ((l1[1].powi(2) + l1[2].powi(2)).sqrt(), (l2[1].powi(2) + l2[2].powi(2)).sqrt());
    let cb = (c1 + c2) / 2.0;
    let g = 0.5 * (1.0 - (cb.powi(7) / (cb.powi(7) + 25f64.powi(7))).sqrt());
    let (a1, a2) = (l1[1] * (1.0 + g), l2[1] * (1.0 + g));
    let (cp1, cp2) = ((a1 * a1 + l1[2] * l1[2]).sqrt(), (a2 * a2 + l2[2] * l2[2]).sqrt());
    let hue = |b: f64, a: f64| if b == 0.0 && a == 0.0 { 0.0 } else { let h = b.atan2(a) / rad; if h < 0.0 { h + 360.0 } else { h } };
    let (h1, h2) = (hue(l1[2], a1), hue(l2[2], a2));
    let dl = l2[0] - l1[0];
    let dc = cp2 - cp1;
    let dh = if cp1 * cp2 == 0.0 { 0.0 } else if (h2 - h1).abs() <= 180.0 { h2 - h1 } else if h2 - h1 > 180.0 { h2 - h1 - 360.0 } else { h2 - h1 + 360.0 };
    let dhh = 2.0 * (cp1 * cp2).sqrt() * (dh * rad / 2.0).sin();
    let lb = (l1[0] + l2[0]) / 2.0;
    let cpb = (cp1 + cp2) / 2.0;
    let hb = if cp1 * cp2 == 0.0 { h1 + h2 } else if (h1 - h2).abs() <= 180.0 { (h1 + h2) / 2.0 } else if h1 + h2 < 360.0 { (h1 + h2 + 360.0) / 2.0 } else { (h1 + h2 - 360.0) / 2.0 };
    let t = 1.0 - 0.17 * ((hb - 30.0) * rad).cos() + 0.24 * ((2.0 * hb) * rad).cos() + 0.32 * ((3.0 * hb + 6.0) * rad).cos() - 0.20 * ((4.0 * hb - 63.0) * rad).cos();
    let dtheta = 30.0 * (-(((hb - 275.0) / 25.0).powi(2))).exp();
    let rc = 2.0 * (cpb.powi(7) / (cpb.powi(7) + 25f64.powi(7))).sqrt();
    let sl = 1.0 + 0.015 * (lb - 50.0).powi(2) / (20.0 + (lb - 50.0).powi(2)).sqrt();
    let sc = 1.0 + 0.045 * cpb;
    let sh = 1.0 + 0.015 * cpb * t;
    let rt = -(2.0 * dtheta * rad).sin() * rc;
    let _ = pi;
    ((dl / sl).powi(2) + (dc / sc).powi(2) + (dhh / sh).powi(2) + rt * (dc / sc) * (dhh / sh)).sqrt()
}

fn cmd_deltae_selftest() {
    // Pares de teste publicados por Sharma et al. (2005): 2,0425 e 2,8615
    let a = delta_e00([50.0, 2.6772, -79.7751], [50.0, 0.0, -82.7485]);
    let b = delta_e00([50.0, 3.1571, -77.2803], [50.0, 0.0, -82.7485]);
    println!("deltae-selftest: par 1 = {:.4} (esperado 2.0425) | par 2 = {:.4} (esperado 2.8615)", a, b);
    assert!((a - 2.0425).abs() < 1e-3 && (b - 2.8615).abs() < 1e-3);
}

// ----------------------------------------------------------------------------- AC-1
fn gen_straight_rgba(w: usize, h: usize) -> Vec<u8> {
    let mut rng = Rng::new(1);
    let mut px = vec![0u8; w * h * 4];
    for (i, p) in px.chunks_exact_mut(4).enumerate() {
        let (x, y) = (i % w, i / w);
        p[0] = (x * 255 / w) as u8;
        p[1] = (y * 255 / h) as u8;
        p[2] = ((x + y) * 255 / (w + h)) as u8;
        // alfa: opaco em metade, e todos os níveis baixos aparecem
        p[3] = match i % 8 {
            0..=3 => 255,
            4 => 0,
            5 => (1 + (rng.next() % 8)) as u8,
            6 => (rng.next() % 256) as u8,
            _ => 254,
        };
        if p[3] == 0 {
            p[0] = (rng.next() % 256) as u8; // cor "escondida" sob alfa 0 (o PNG a preserva)
        }
    }
    px
}
fn png_encode(px: &[u8], w: u32, h: u32) -> R<Vec<u8>> {
    let mut out = Vec::new();
    {
        let mut e = png::Encoder::new(&mut out, w, h);
        e.set_color(png::ColorType::Rgba);
        e.set_depth(png::BitDepth::Eight);
        e.write_header()?.write_image_data(px)?;
    }
    Ok(out)
}
fn png_decode(bytes: &[u8]) -> R<(Vec<u8>, u32, u32)> {
    let mut d = png::Decoder::new(Cursor::new(bytes));
    d.set_transformations(png::Transformations::IDENTITY);
    let mut r = d.read_info()?;
    let mut buf = vec![0u8; r.output_buffer_size().ok_or("tamanho")?];
    let info = r.next_frame(&mut buf)?;
    buf.truncate(info.buffer_size());
    Ok((buf, info.width, info.height))
}
fn diff_stats(a: &[u8], b: &[u8]) -> (usize, u8, usize) {
    let (mut px_diff, mut max, mut ch_diff) = (0usize, 0u8, 0usize);
    for (x, y) in a.chunks_exact(4).zip(b.chunks_exact(4)) {
        let mut d = false;
        for k in 0..4 {
            let e = x[k].abs_diff(y[k]);
            if e > 0 {
                d = true;
                ch_diff += 1;
                max = max.max(e);
            }
        }
        if d {
            px_diff += 1;
        }
    }
    (px_diff, max, ch_diff)
}
fn premul8(p: [u8; 4]) -> [u8; 4] {
    let a = p[3] as u32;
    [((p[0] as u32 * a + 127) / 255) as u8, ((p[1] as u32 * a + 127) / 255) as u8, ((p[2] as u32 * a + 127) / 255) as u8, p[3]]
}
fn unpremul8(p: [u8; 4]) -> [u8; 4] {
    let a = p[3] as u32;
    if a == 0 {
        return [0, 0, 0, 0];
    }
    [((p[0] as u32 * 255 + a / 2) / a).min(255) as u8, ((p[1] as u32 * 255 + a / 2) / a).min(255) as u8, ((p[2] as u32 * 255 + a / 2) / a).min(255) as u8, p[3]]
}
fn premul16(p: [u8; 4]) -> [u16; 4] {
    // 8 -> 16 bits (x*257) e pré-multiplicação em 16 bits
    let a = p[3] as u32 * 257;
    let c = |v: u8| ((v as u32 * 257 * a + 32767) / 65535) as u16;
    [c(p[0]), c(p[1]), c(p[2]), a as u16]
}
fn unpremul16_to8(p: [u16; 4]) -> [u8; 4] {
    let a = p[3] as u32;
    if a == 0 {
        return [0, 0, 0, 0];
    }
    let c = |v: u16| {
        let straight16 = ((v as u32 * 65535 + a / 2) / a).min(65535);
        ((straight16 + 128) / 257).min(255) as u8
    };
    [c(p[0]), c(p[1]), c(p[2]), ((a + 128) / 257) as u8]
}

fn cmd_ac1() -> R<()> {
    let (w, h) = (1024usize, 1024usize);
    let straight = gen_straight_rgba(w, h);
    // importa (PNG -> pixels) como o app faria
    let png_in = png_encode(&straight, w as u32, h as u32)?;
    let (imported, _, _) = png_decode(&png_in)?;
    assert_eq!(imported, straight, "o PNG em si deve ser sem perdas");

    // Caminho A: tiles em alfa DIRETO (sem pré-multiplicar), 8 bits
    let a_out = imported.clone();
    let (d, m, _) = diff_stats(&a_out, &straight);
    println!("AC-1 caminho A (alfa direto, 8 bits, sem conversão): pixels diferentes = {} | erro máx = {}", d, m);

    // Caminho B: alfa pré-multiplicado em 8 bits (o que o ADR-013 descreve, em 8 bits)
    let mut b_out = Vec::with_capacity(imported.len());
    for p in imported.chunks_exact(4) {
        b_out.extend_from_slice(&unpremul8(premul8([p[0], p[1], p[2], p[3]])));
    }
    let (d, m, _) = diff_stats(&b_out, &straight);
    println!("AC-1 caminho B (pré-multiplicado, 8 bits): pixels diferentes = {} ({:.2}%) | erro máx = {}", d, d as f64 * 100.0 / (w * h) as f64, m);
    // detalhe só nos opacos
    let opaque_diff = imported.chunks_exact(4).zip(b_out.chunks_exact(4)).filter(|(x, y)| x[3] == 255 && x != y).count();
    println!("    entre os pixels com alfa = 255: diferentes = {}", opaque_diff);
    let hidden = imported.chunks_exact(4).zip(b_out.chunks_exact(4)).filter(|(x, y)| x[3] == 0 && x[..3] != y[..3]).count();
    println!("    cor sob alfa 0 perdida em {} pixels (esperado: pré-multiplicar descarta)", hidden);

    // Caminho C: pré-multiplicado em 16 bits
    let mut c_out = Vec::with_capacity(imported.len());
    for p in imported.chunks_exact(4) {
        c_out.extend_from_slice(&unpremul16_to8(premul16([p[0], p[1], p[2], p[3]])));
    }
    let (d, m, _) = diff_stats(&c_out, &straight);
    println!("AC-1 caminho C (pré-multiplicado, 16 bits interno, volta a 8): pixels diferentes = {} ({:.2}%) | erro máx = {}", d, d as f64 * 100.0 / (w * h) as f64, m);
    let opaque_diff = imported.chunks_exact(4).zip(c_out.chunks_exact(4)).filter(|(x, y)| x[3] == 255 && x != y).count();
    println!("    entre os pixels com alfa = 255: diferentes = {}", opaque_diff);

    // Exportação PNG do caminho A e releitura
    let png_out = png_encode(&a_out, w as u32, h as u32)?;
    let (re, _, _) = png_decode(&png_out)?;
    println!("AC-1 ida e volta completa (PNG -> tiles direto -> PNG -> leitura): idêntico bit a bit = {}", re == straight);

    // A biblioteca de cor, sRGB -> sRGB (espaço de trabalho = perfil de origem), é identidade?
    let srgb = ColorProfile::new_srgb();
    let tr = srgb.create_transform_8bit(Layout::Rgba, &srgb, Layout::Rgba, TransformOptions::default())?;
    let mut src = Vec::with_capacity(256 * 256 * 4);
    for r in 0..256u32 {
        for g in 0..256u32 {
            src.extend_from_slice(&[r as u8, g as u8, ((r * 7 + g * 13) % 256) as u8, 255]);
        }
    }
    let mut dst = vec![0u8; src.len()];
    tr.transform(&src, &mut dst)?;
    let (d, m, _) = diff_stats(&src, &dst);
    println!("AC-1 moxcms sRGB->sRGB 8 bits ({} cores): pixels alterados = {} | erro máx = {}", src.len() / 4, d, m);
    Ok(())
}

// ----------------------------------------------------------------------------- AC-2
fn lcms_p3() -> R<lcms2::Profile> {
    use lcms2::{CIExyY, CIExyYTRIPLE, Profile, ToneCurve};
    let white = CIExyY { x: 0.3127, y: 0.3290, Y: 1.0 };
    let prim = CIExyYTRIPLE { Red: CIExyY { x: 0.680, y: 0.320, Y: 1.0 }, Green: CIExyY { x: 0.265, y: 0.690, Y: 1.0 }, Blue: CIExyY { x: 0.150, y: 0.060, Y: 1.0 } };
    let curve = ToneCurve::new_parametric(4, &[2.4, 1.0 / 1.055, 0.055 / 1.055, 1.0 / 12.92, 0.04045])?;
    Ok(Profile::new_rgb(&white, &prim, &[&curve, &curve, &curve])?)
}

struct Stat {
    name: String,
    n: usize,
    max: f64,
    sum: f64,
    over1: usize,
    vals: Vec<f64>,
}
impl Stat {
    fn new(name: &str) -> Self {
        Stat { name: name.into(), n: 0, max: 0.0, sum: 0.0, over1: 0, vals: Vec::new() }
    }
    fn add(&mut self, v: f64) {
        self.n += 1;
        self.sum += v;
        if v > self.max {
            self.max = v;
        }
        if v > 1.0 {
            self.over1 += 1;
        }
        self.vals.push(v);
    }
    fn report(&mut self) {
        self.vals.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let p = |q: f64| self.vals[((self.vals.len() as f64 * q) as usize).min(self.vals.len() - 1)];
        println!("  {:<34} n={:<8} ΔE00 médio={:.4} p99={:.4} p99,9={:.4} máx={:.4} | acima de 1: {}", self.name, self.n, self.sum / self.n as f64, p(0.99), p(0.999), self.max, self.over1);
    }
}

fn cmd_ac2() -> R<()> {
    let p3 = ColorProfile::new_display_p3();
    let srgb = ColorProfile::new_srgb();
    let opts = TransformOptions { rendering_intent: RenderingIntent::RelativeColorimetric, ..TransformOptions::default() };
    let opts_float = TransformOptions { rendering_intent: RenderingIntent::RelativeColorimetric, prefer_fixed_point: false, ..TransformOptions::default() };
    let mox8 = p3.create_transform_8bit(Layout::Rgba, &srgb, Layout::Rgba, opts)?;
    let mox8f = p3.create_transform_8bit(Layout::Rgba, &srgb, Layout::Rgba, opts_float)?;
    let mox8p = p3.create_transform_8bit(Layout::Rgba, &srgb, Layout::Rgba, TransformOptions::default())?;
    let mox16 = p3.create_transform_16bit(Layout::Rgba, &srgb, Layout::Rgba, opts)?;
    let l_p3 = lcms_p3()?;
    let l_srgb = lcms2::Profile::new_srgb();
    let l8 = lcms2::Transform::new(&l_p3, lcms2::PixelFormat::RGBA_8, &l_srgb, lcms2::PixelFormat::RGBA_8, lcms2::Intent::RelativeColorimetric)?;
    let l16 = lcms2::Transform::new(&l_p3, lcms2::PixelFormat::RGBA_16, &l_srgb, lcms2::PixelFormat::RGBA_16, lcms2::Intent::RelativeColorimetric)?;

    // amostras: grade 33^3 + 200.000 aleatórias, em P3 codificado
    let mut samples: Vec<[f64; 3]> = Vec::new();
    for r in 0..33 {
        for g in 0..33 {
            for b in 0..33 {
                samples.push([r as f64 / 32.0, g as f64 / 32.0, b as f64 / 32.0]);
            }
        }
    }
    let mut rng = Rng::new(99);
    for _ in 0..200_000 {
        samples.push([rng.f(), rng.f(), rng.f()]);
    }
    let in_gamut = |e: [f64; 3]| e.iter().all(|v| *v >= -0.0005 && *v <= 1.0005);
    let n_in = samples.iter().filter(|s| in_gamut(p3_to_srgb_exact(**s))).count();
    println!("AC-2: {} cores P3 amostradas; {} ({:.1}%) caem DENTRO do gamut sRGB e {} fora", samples.len(), n_in, n_in as f64 * 100.0 / samples.len() as f64, samples.len() - n_in);

    let q8 = |v: f64| (v * 255.0).round().clamp(0.0, 255.0) as u8;
    let q16 = |v: f64| (v * 65535.0).round().clamp(0.0, 65535.0) as u16;
    let mut st = vec![Stat::new("moxcms 8 bits RelCol+ponto fixo"), Stat::new("moxcms 16 bits RelCol"), Stat::new("lcms2 8 bits (dentro do gamut)"), Stat::new("lcms2 16 bits (dentro do gamut)"), Stat::new("quantização 8 bits ideal (piso)"), Stat::new("moxcms 8 bits FORA do gamut (recorte)"), Stat::new("moxcms 8 bits RelCol+ponto flutuante"), Stat::new("moxcms 8 bits padrão (Perceptual)")];
    for s in &samples {
        let exact = p3_to_srgb_exact(*s);
        let lab_ref = srgb_to_lab(exact);
        let inside = in_gamut(exact);
        let src8 = [q8(s[0]), q8(s[1]), q8(s[2]), 255u8];
        let src16 = [q16(s[0]), q16(s[1]), q16(s[2]), 65535u16];
        // referência exata para a MESMA entrada quantizada
        let in8 = [src8[0] as f64 / 255.0, src8[1] as f64 / 255.0, src8[2] as f64 / 255.0];
        let in16 = [src16[0] as f64 / 65535.0, src16[1] as f64 / 65535.0, src16[2] as f64 / 65535.0];
        let ref8 = p3_to_srgb_exact(in8);
        let ref16 = p3_to_srgb_exact(in16);
        let (ref8_in, ref16_in) = (in_gamut(ref8), in_gamut(ref16));
        let clip = |v: [f64; 3]| [v[0].clamp(0.0, 1.0), v[1].clamp(0.0, 1.0), v[2].clamp(0.0, 1.0)];

        let mut o8 = [0u8; 4];
        mox8.transform(&src8, &mut o8)?;
        let mut o8f = [0u8; 4];
        mox8f.transform(&src8, &mut o8f)?;
        let mut o8p = [0u8; 4];
        mox8p.transform(&src8, &mut o8p)?;
        let mut o16 = [0u16; 4];
        mox16.transform(&src16, &mut o16)?;
        let mut lo8 = [[0u8; 4]];
        l8.transform_pixels(&[src8], &mut lo8);
        let mut lo16 = [[0u16; 4]];
        l16.transform_pixels(&[src16], &mut lo16);
        let to_lab8 = |p: [u8; 4]| srgb_to_lab([p[0] as f64 / 255.0, p[1] as f64 / 255.0, p[2] as f64 / 255.0]);
        let to_lab16 = |p: [u16; 4]| srgb_to_lab([p[0] as f64 / 65535.0, p[1] as f64 / 65535.0, p[2] as f64 / 65535.0]);
        if ref8_in {
            st[0].add(delta_e00(srgb_to_lab(ref8), to_lab8(o8)));
            st[2].add(delta_e00(srgb_to_lab(ref8), to_lab8(lo8[0])));
            st[6].add(delta_e00(srgb_to_lab(ref8), to_lab8(o8f)));
            st[7].add(delta_e00(srgb_to_lab(ref8), to_lab8(o8p)));
            st[4].add(delta_e00(srgb_to_lab(ref8), srgb_to_lab([q8(ref8[0]) as f64 / 255.0, q8(ref8[1]) as f64 / 255.0, q8(ref8[2]) as f64 / 255.0])));
        } else {
            st[5].add(delta_e00(srgb_to_lab(clip(ref8)), to_lab8(o8)));
        }
        if ref16_in {
            st[1].add(delta_e00(srgb_to_lab(ref16), to_lab16(o16)));
            st[3].add(delta_e00(srgb_to_lab(ref16), to_lab16(lo16[0])));
        }
        let _ = (lab_ref, inside);
    }
    println!("ΔE00 da conversão P3 -> sRGB contra a referência matemática em ponto flutuante (f64):");
    for s in st.iter_mut() {
        if s.n > 0 {
            s.report();
        }
    }
    println!("  (a linha 'FORA do gamut' compara o resultado recortado da biblioteca com o recorte ideal; cores P3 fora do sRGB não têm representação exata)");
    Ok(())
}

// ----------------------------------------------------------------------------- AC-4
fn cmd_ac4() -> R<()> {
    let ddl = include_str!("../../../../contracts/document-format/rbsc-schema-v1.sql");
    let icc = ColorProfile::new_display_p3().encode()?;
    let path = std::env::temp_dir().join("spike-d-ac4.rbsc");
    for s in ["", "-wal", "-shm"] {
        let _ = std::fs::remove_file(format!("{}{}", path.display(), s));
    }
    // tile RGBA16 de teste
    let mut rng = Rng::new(5);
    let tile16: Vec<u8> = (0..256 * 256 * 8).map(|_| (rng.next() % 251) as u8).collect();
    let hash = [7u8; 32];
    {
        let c = Connection::open(&path)?;
        c.query_row("PRAGMA journal_mode=WAL", [], |r| r.get::<_, String>(0))?;
        c.execute_batch(ddl)?;
        c.execute("INSERT INTO document_meta(doc_id,width,height,dpi,color_profile,bit_depth,blend_space) VALUES(x'01',4096,4096,300,?,16,'linear')", params![icc.clone()])?;
        c.execute("INSERT INTO tiles(hash,codec,raw_len,data) VALUES(?,'zstd',?,?)", params![hash.to_vec(), tile16.len() as i64, zstd::bulk::compress(&tile16, 3)?])?;
    }
    // reabre em outra conexão
    let c = Connection::open(&path)?;
    let (depth, space, blob): (i64, String, Vec<u8>) = c.query_row("SELECT bit_depth,blend_space,color_profile FROM document_meta", [], |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)))?;
    let (raw_len, data): (i64, Vec<u8>) = c.query_row("SELECT raw_len,data FROM tiles WHERE hash=?", params![hash.to_vec()], |r| Ok((r.get(0)?, r.get(1)?)))?;
    let back = zstd::bulk::decompress(&data, raw_len as usize)?;
    println!("AC-4: perfil ICC ({} bytes) idêntico = {} | profundidade = {} | espaço de mesclagem = {} | tile RGBA16 ({} KiB) idêntico = {}", icc.len(), blob == icc, depth, space, raw_len / 1024, back == tile16);
    let reread = ColorProfile::new_from_slice(&blob)?;
    println!("      perfil relido é aceito pela biblioteca e é RGB = {}", format!("{:?}", reread.color_space).contains("Rgb"));
    // o contrato recusa valores inválidos?
    let bad_depth = c.execute("INSERT INTO document_meta(doc_id,width,height,dpi,color_profile,bit_depth,blend_space) VALUES(x'02',1,1,72,x'00',12,'linear')", []);
    let bad_space = c.execute("INSERT INTO document_meta(doc_id,width,height,dpi,color_profile,bit_depth,blend_space) VALUES(x'03',1,1,72,x'00',8,'hsl')", []);
    println!("      o schema recusa bit_depth=12: {} | blend_space='hsl': {}", bad_depth.is_err(), bad_space.is_err());
    Ok(())
}

// ----------------------------------------------------------------------------- memória
fn cmd_mem() {
    let mib = |b: f64| b / 1048576.0;
    let tile8 = 256.0 * 256.0 * 4.0;
    let tile16 = tile8 * 2.0;
    println!("Custo de memória (tile 256x256): RGBA8 = {:.0} KiB | RGBA16 = {:.0} KiB", tile8 / 1024.0, tile16 / 1024.0);
    for (name, w, h, layers) in [("R-A (4096x4096, 30 camadas)", 4096.0, 4096.0, 30.0), ("R-B (8192x8192, 10 camadas)", 8192.0, 8192.0, 10.0)] {
        let tiles = (w / 256.0) * (h / 256.0) * layers;
        println!("  {name}: {tiles:.0} tiles se 100% preenchido | 8 bits = {:.0} MiB | 16 bits = {:.0} MiB", mib(tiles * tile8), mib(tiles * tile16));
    }
    println!("Conjunto de trabalho de um viewport de tablet (2048x1536 px = 8x6 = 48 tiles) com N camadas visíveis:");
    for layers in [5.0, 10.0, 30.0] {
        let t = 48.0 * layers;
        println!("  {layers:>2.0} camadas visíveis: {t:.0} tiles | 8 bits = {:.0} MiB | 16 bits = {:.0} MiB", mib(t * tile8), mib(t * tile16));
    }
    println!("Orçamento de cache de tiles em tablet (design da SPEC-002): 256 MiB = {:.0} tiles RGBA8 ou {:.0} tiles RGBA16", 256.0 * 1048576.0 / tile8, 256.0 * 1048576.0 / tile16);
    println!("Observação: o 'iPad de referência' ainda não existe (DEC-004 está Aberta); os números acima são aritmética, não medição em um aparelho.");
}

// ----------------------------------------------------------------------------- composição (CPU)
fn compose_u8(layers: &[Vec<u8>], out: &mut [u8], threads: usize) {
    let chunk = out.len().div_ceil(threads) / 4 * 4;
    std::thread::scope(|s| {
        for (ci, o) in out.chunks_mut(chunk).enumerate() {
            s.spawn(move || {
                let base = ci * chunk;
                for px in o.chunks_exact_mut(4) {
                    px.copy_from_slice(&[0, 0, 0, 0]);
                }
                for l in layers {
                    let src = &l[base..base + o.len()];
                    for (d, s) in o.chunks_exact_mut(4).zip(src.chunks_exact(4)) {
                        let ia = 255 - s[3] as u32; // pré-multiplicado: out = src + dst*(1-sa)
                        for k in 0..4 {
                            d[k] = (s[k] as u32 + (d[k] as u32 * ia + 127) / 255).min(255) as u8;
                        }
                    }
                }
            });
        }
    });
}
fn compose_u16(layers: &[Vec<u16>], out: &mut [u16], threads: usize) {
    let chunk = out.len().div_ceil(threads) / 4 * 4;
    std::thread::scope(|s| {
        for (ci, o) in out.chunks_mut(chunk).enumerate() {
            s.spawn(move || {
                let base = ci * chunk;
                for v in o.iter_mut() {
                    *v = 0;
                }
                for l in layers {
                    let src = &l[base..base + o.len()];
                    for (d, s) in o.chunks_exact_mut(4).zip(src.chunks_exact(4)) {
                        let ia = 65535 - s[3] as u32;
                        for k in 0..4 {
                            d[k] = (s[k] as u32 + (d[k] as u32 * ia + 32767) / 65535).min(65535) as u16;
                        }
                    }
                }
            });
        }
    });
}
/// Mesclagem em espaço LINEAR a partir de camadas codificadas em sRGB: decodifica cada camada (LUT), mescla e recodifica.
fn compose_linear_u16(layers: &[Vec<u16>], out: &mut [u16], dec: &[u16], enc: &[u16], threads: usize) {
    let chunk = out.len().div_ceil(threads) / 4 * 4;
    std::thread::scope(|s| {
        for (ci, o) in out.chunks_mut(chunk).enumerate() {
            s.spawn(move || {
                let base = ci * chunk;
                for v in o.iter_mut() {
                    *v = 0;
                }
                for l in layers {
                    let src = &l[base..base + o.len()];
                    for (d, s) in o.chunks_exact_mut(4).zip(src.chunks_exact(4)) {
                        let a = s[3] as u32;
                        let ia = 65535 - a;
                        for k in 0..3 {
                            // desfaz o pré-multiplicado, decodifica, refaz o pré-multiplicado em linear
                            let straight = if a == 0 { 0 } else { ((s[k] as u32 * 65535 + a / 2) / a).min(65535) };
                            let lin = dec[straight as usize] as u32;
                            let pm = (lin * a + 32767) / 65535;
                            d[k] = (pm + (d[k] as u32 * ia + 32767) / 65535).min(65535) as u16;
                        }
                        d[3] = (a + (d[3] as u32 * ia + 32767) / 65535).min(65535) as u16;
                    }
                }
                // codifica o resultado de volta (desfaz o pré-multiplicado, aplica a curva)
                for d in o.chunks_exact_mut(4) {
                    let a = d[3] as u32;
                    for k in 0..3 {
                        let straight = if a == 0 { 0 } else { ((d[k] as u32 * 65535 + a / 2) / a).min(65535) };
                        d[k] = enc[straight as usize];
                    }
                }
            });
        }
    });
}

fn cmd_compose() {
    let (w, h, nl) = (2048usize, 1536usize, 30usize); // viewport de tablet com 30 camadas
    let n = w * h * 4;
    let mut rng = Rng::new(3);
    let l8: Vec<Vec<u8>> = (0..nl).map(|_| {
        let mut v = Vec::with_capacity(n);
        for _ in 0..n / 4 {
            let a = (rng.next() % 256) as u32;
            for _ in 0..3 {
                v.push(((rng.next() % 256) as u32 * a / 255) as u8);
            }
            v.push(a as u8);
        }
        v
    }).collect();
    let l16: Vec<Vec<u16>> = l8.iter().map(|l| l.iter().map(|v| *v as u16 * 257).collect()).collect();
    let dec: Vec<u16> = (0..65536).map(|i| (srgb_decode(i as f64 / 65535.0) * 65535.0).round() as u16).collect();
    let enc: Vec<u16> = (0..65536).map(|i| (srgb_encode(i as f64 / 65535.0) * 65535.0).round() as u16).collect();
    let mut o8 = vec![0u8; n];
    let mut o16 = vec![0u16; n];
    let cores = std::thread::available_parallelism().map(|v| v.get()).unwrap_or(1);
    println!("Composição em CPU de {nl} camadas, viewport {w}x{h} (alfa pré-multiplicado, 'normal'); {cores} threads lógicas. Mediana de 7 execuções:");
    let med = |f: &mut dyn FnMut()| {
        let mut v: Vec<f64> = (0..7).map(|_| { let t = Instant::now(); f(); t.elapsed().as_secs_f64() * 1000.0 }).collect();
        v.sort_by(|a, b| a.partial_cmp(b).unwrap());
        v[3]
    };
    for threads in [1, cores] {
        let a = med(&mut || compose_u8(&l8, &mut o8, threads));
        let b = med(&mut || compose_u16(&l16, &mut o16, threads));
        let c = med(&mut || compose_linear_u16(&l16, &mut o16, &dec, &enc, threads));
        println!("  {threads:>2} thread(s): RGBA8 perceptual = {a:.1} ms | RGBA16 perceptual = {b:.1} ms | RGBA16 linear (LUT) = {c:.1} ms");
    }
    println!("Atenção: é CPU escalar. O custo real virá da GPU (spike a); isto só compara 8 e 16 bits sob as mesmas condições.");
}

fn cmd_probe() -> R<()> {
    let p3 = ColorProfile::new_display_p3();
    let srgb = ColorProfile::new_srgb();
    println!("TransformOptions::default() = {:?}", TransformOptions::default());
    let mox8 = p3.create_transform_8bit(Layout::Rgba, &srgb, Layout::Rgba, TransformOptions::default())?;
    let mut worst: Vec<(f64, [u8; 3], [u8; 3])> = Vec::new();
    for r in 0..256u32 {
        for g in (0..256u32).step_by(3) {
            for b in (0..256u32).step_by(3) {
                let src = [r as u8, g as u8, b as u8, 255u8];
                let exact = p3_to_srgb_exact([r as f64 / 255.0, g as f64 / 255.0, b as f64 / 255.0]);
                if !exact.iter().all(|v| *v >= 0.0 && *v <= 1.0) {
                    continue;
                }
                let mut o = [0u8; 4];
                mox8.transform(&src, &mut o)?;
                let d = delta_e00(srgb_to_lab(exact), srgb_to_lab([o[0] as f64 / 255.0, o[1] as f64 / 255.0, o[2] as f64 / 255.0]));
                if d > 0.95 {
                    worst.push((d, [src[0], src[1], src[2]], [o[0], o[1], o[2]]));
                }
            }
        }
    }
    worst.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
    println!("moxcms 8 bits com ΔE00 > 0,95 (varredura de 256x86x86): {} casos; piores:", worst.len());
    for w in worst.iter().take(6) {
        println!("  P3 {:?} -> sRGB obtido {:?} | ΔE00 = {:.3}", w.1, w.2, w.0);
    }
    Ok(())
}

fn main() -> R<()> {
    match std::env::args().nth(1).as_deref() {
        Some("deltae-selftest") => cmd_deltae_selftest(),
        Some("ac1") => cmd_ac1()?,
        Some("ac2") => cmd_ac2()?,
        Some("ac4") => cmd_ac4()?,
        Some("mem") => cmd_mem(),
        Some("probe") => cmd_probe()?,
        Some("compose") => cmd_compose(),
        _ => {
            eprintln!("uso: deltae-selftest | ac1 | ac2 | ac4 | mem | compose");
            std::process::exit(2);
        }
    }
    Ok(())
}
