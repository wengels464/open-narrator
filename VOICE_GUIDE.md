# Voice Quality Improvement Guide

## Available Voices (54 total)

### English Adult Voices (Recommended for Audiobooks)
**Female (af_*):**
- `af_bella` - Clear, professional tone
- `af_nicole` - Warm, conversational
- `af_sarah` - Balanced, neutral (current default)
- `af_nova` - Expressive, dynamic
- `af_jessica` - Smooth, pleasant
- `af_alloy`, `af_aoede`, `af_heart`, `af_kore`, `af_river`, `af_sky`

**Male (am_*):**
- `am_adam` - Deep, authoritative
- `am_michael` - Clear, professional
- `am_liam` - Natural, friendly
- `am_echo` - Expressive, engaging
- `am_eric`, `am_fenrir`, `am_onyx`, `am_puck`, `am_santa`

### Other Languages
- **British English (bf_*, bm_*)**: alice, emma, isabella, lily, daniel, fable, george, lewis
- **Spanish (ef_*, em_*)**: dora, alex, santa
- **French (ff_*)**: siwis
- **Hindi (hf_*, hm_*)**: alpha, beta, omega, psi
- **Italian (if_*, im_*)**: sara, nicola
- **Japanese (jf_*, jm_*)**: alpha, gongitsune, nezumi, tebukuro, kumo
- **Portuguese (pf_*, pm_*)**: dora, alex, santa
- **Chinese (zf_*, zm_*)**: xiaobei, xiaoni, xiaoxiao, xiaoyi, yunjian, yunxi, yunxia, yunyang

## Speed Settings for Better Naturalness

The `--speed` parameter controls narration pace:
- `0.8` - Slower, more deliberate (good for technical content)
- `0.9` - Slightly slower, natural pacing
- `1.0` - Default speed (current)
- `1.1` - Slightly faster, energetic
- `1.2` - Faster (may sound rushed)

**Recommendation**: Try `0.9` for a more natural, audiobook-like pace.

## Testing Different Voices

### Quick Test (5 voices × 4 speeds = 20 samples)
```bash
py -3.10 test_voices.py
```

### Custom Test
```bash
# Test specific voices
py -3.10 test_voices.py -v af_bella af_nicole am_adam am_michael

# Test specific speeds
py -3.10 test_voices.py -s 0.85 0.9 0.95 1.0

# Custom text
py -3.10 test_voices.py -t "Your sample text here"
```

### Generate Full Audiobook with Better Settings
```bash
# Example with af_bella at 0.9 speed
py -3.10 src/cli.py "samples/your_book.epub" -o output.m4b -v af_bella -s 0.9
```

## Recommended Combinations for Audiobooks

1. **Professional Female**: `af_bella` at speed `0.9`
2. **Warm Female**: `af_nicole` at speed `0.95`
3. **Expressive Female**: `af_nova` at speed `0.9`
4. **Professional Male**: `am_michael` at speed `0.9`
5. **Authoritative Male**: `am_adam` at speed `0.85`
6. **Friendly Male**: `am_liam` at speed `0.95`

## Advanced: Future Enhancements

For even better naturalness, future versions could add:
- Pause insertion at sentence boundaries
- Prosody adjustments for questions vs statements
- Chapter-aware pacing (slower for important sections)
- Emotion/tone control (if supported by model)
