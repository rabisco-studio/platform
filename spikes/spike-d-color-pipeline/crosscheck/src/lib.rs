//! Converte um pixel Display P3 para sRGB com a biblioteca escolhida (só para provar que compila no alvo).
#[cfg(feature = "moxcms")]
pub fn p3_to_srgb_8(px: &[u8], out: &mut [u8]) -> Result<(), String> {
    use moxcms::{ColorProfile, Layout, TransformOptions};
    let t = ColorProfile::new_display_p3()
        .create_transform_8bit(Layout::Rgba, &ColorProfile::new_srgb(), Layout::Rgba, TransformOptions::default())
        .map_err(|e| format!("{e:?}"))?;
    t.transform(px, out).map_err(|e| format!("{e:?}"))
}

#[cfg(feature = "lcms2")]
pub fn lcms_srgb_profile() -> lcms2::Profile {
    lcms2::Profile::new_srgb()
}
