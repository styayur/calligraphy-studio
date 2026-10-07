import type { CandidatePolicy, ExplorationMode } from '../../lib/candidatePolicy'

export function SourcePolicyControls({ policy, onChange }: { policy: CandidatePolicy; onChange: (value: CandidatePolicy) => void }) {
  const update = (key: keyof CandidatePolicy, value: string) => onChange({ ...policy, [key]: value || undefined })
  return <div className="source-policy">
    <div className="field-grid">
      <label>传统 / Tradition
        <select aria-label="Tradition" value={policy.writing_tradition || 'Chinese'} onChange={(e) => onChange({ writing_tradition: e.target.value, locale: e.target.value === 'Japanese' ? 'ja-JP' : undefined, mode: 'strict' })}>
          <option value="Chinese">Chinese · 中文</option><option value="Japanese">Japanese · 日本</option>
        </select>
      </label>
      <label>文字 / Script
        <select aria-label="Script" value={policy.script || ''} onChange={(e) => update('script',e.target.value)}>
          <option value="">全部 / All scripts</option><option value="Han">漢字 / Han · Kanji</option>
          {policy.writing_tradition === 'Japanese' && <><option value="Hiragana">ひらがな / Hiragana</option><option value="Katakana">カタカナ / Katakana</option></>}
        </select>
      </label>
    </div>
    <details className="advanced">
      <summary>字形与跨传统探索 / Variants & exploration</summary>
      <label>语言 / Language<select aria-label="Language" value={policy.language || ''} onChange={(e) => update('language',e.target.value)}><option value="">未限定 / Any or unknown</option><option value="zh">中文 / zh</option><option value="ja">日本語 / ja</option></select></label>
      <label>选择规则 / Candidate mode
        <select aria-label="Candidate mode" value={policy.mode || 'strict'} onChange={(e) => onChange({ ...policy, mode: e.target.value as ExplorationMode })}>
          <option value="strict">严格传统 / Strict tradition</option><option value="related">相关字形 / Related variants</option><option value="cross-tradition">跨传统探索 / Cross-tradition exploration</option>
        </select>
      </label>
      <label>字形变体 / Variant
        <select aria-label="Variant type" value={policy.variant_type || ''} onChange={(e) => update('variant_type',e.target.value)}>
          <option value="">默认 / Default variants</option>
          <option value="regional">地区字形 / Regional</option>
          <option value="historical">くずし字 / Historical glyphs</option>
          <option value="hentaigana">変体仮名 / Hentaigana</option>
          <option value="shinjitai">新字体 / Shinjitai</option><option value="kyujitai">旧字体 / Kyūjitai</option>
          <option value="simplified">简体 / Simplified</option><option value="traditional">繁体 / Traditional</option>
        </select>
      </label>
      <label>区域 / Locale
        <select aria-label="Locale" value={policy.locale || ''} onChange={(e) => update('locale',e.target.value)}>
          <option value="">未指定 / Unspecified</option><option value="ja-JP">日本 / ja-JP</option><option value="zh-Hans">简体中文 / zh-Hans</option><option value="zh-Hant">繁体中文 / zh-Hant</option>
        </select>
      </label>
      <label>时期 / Period<input aria-label="Period" value={policy.period || ''} onChange={(e) => update('period',e.target.value)} /></label>
      <label>作品 / Work<input aria-label="Work" value={policy.work || ''} onChange={(e) => update('work',e.target.value)} placeholder="Yuji Mai / ぢぐち" /></label>
      <label>书家或设计师 / Author<input aria-label="Designer" value={policy.designer || ''} onChange={(e) => update('designer',e.target.value)} /></label>
      <label className="check-field"><input type="checkbox" checked={policy.commercial_only || false} onChange={(e) => onChange({ ...policy, commercial_only: e.target.checked })} />仅明确允许商用 / Commercially permitted</label>
    </details>
    {policy.mode === 'cross-tradition' && <p className="field-hint">跨传统候选需逐字复核。Shared Unicode does not imply regional compatibility.</p>}
  </div>
}
