/* Created and led by Kamden Higgs. No engineering equations live in this panel. */
const mountedPanels = new WeakMap();
export function renderPanel(target, data) {
  // InvenTree re-invokes legacy panels when its context object refreshes.
  // Keep this same container's DOM and in-flight handlers for the same user/part.
  const identity = JSON.stringify([data.id, data.user?.pk ?? data.user?.id]);
  const previous = mountedPanels.get(target);
  if (previous?.identity === identity) { target.replaceChildren(previous.node); return; }
  const base = new URL('/plugin/higgs-camera-review/', window.location.origin).href;
  const api = data.api;
  const current = data.id;
  const selectionKey = 'higgs-review-open:' + identity;
  let assessment = null;
  let options = [];
  target.innerHTML = `<section class="higgs-review">
  <style>
  .higgs-review{color:#172d37;background:#f6f8f7;border:1px solid #d8e1df;border-radius:12px;padding:24px;font:14px/1.5 system-ui;max-width:1120px}
  .higgs-review h2{font-size:26px;letter-spacing:-.8px;margin:6px 0}.higgs-review h3{font-size:17px;margin:18px 0 8px}.higgs-review p{margin:6px 0}.higgs-review .eyebrow{letter-spacing:2px;font-size:11px;font-weight:750;color:#386c64}
  .higgs-review .notice{border-left:3px solid #287d6c;background:#e6f1ed;padding:10px 14px;margin:16px 0}.higgs-review .row{display:flex;gap:12px;align-items:end;flex-wrap:wrap}.higgs-review label{display:flex;flex-direction:column;gap:5px;font-weight:600}.higgs-review input,.higgs-review select{font:inherit;background:white;color:#172d37;border:1px solid #a5bab3;border-radius:6px;padding:9px;max-width:100%}
  .higgs-review button{font:inherit;border:1px solid #165e51;background:#165e51;color:white;padding:10px 15px;border-radius:6px;cursor:pointer}.higgs-review button.secondary{background:white;color:#165e51}.higgs-review button:disabled{opacity:.5;cursor:wait}.higgs-review .small{font-size:12px;color:#4b626c}.higgs-review .badge{display:inline-block;padding:5px 10px;border-radius:5px;background:#e6eee9;font-weight:700;margin:0 5px 6px 0}.higgs-review .warn{background:#ffe6bd;color:#713d03}.higgs-review .bad{background:#fce0dc;color:#862f20}
  .higgs-review table{width:100%;border-collapse:collapse;background:white;margin:12px 0}.higgs-review th,.higgs-review td{text-align:left;padding:9px 12px;border-bottom:1px solid #e0e7e4}.higgs-review pre{white-space:pre-wrap;word-break:break-word;font-size:12px;padding:12px;background:#eaf0ed;max-height:360px;overflow:auto}.higgs-review .result{margin-top:24px;border-top:1px solid #ccd9d3;padding-top:18px}.higgs-review details{margin:12px 0}.higgs-review summary{cursor:pointer;font-weight:600}.higgs-review .error{color:#862f20;white-space:pre-wrap}.higgs-review .question{padding:14px;background:#fff;border:1px solid #d8e1df;border-radius:8px}
  </style>
  <div class="eyebrow">HIGGS AI / EXPERIMENTAL INTEGRATION 0.1.3</div>
  <h2>Camera substitution review</h2>
  <p>Keep the evidence with the decision.</p>
  <div class="notice"><strong>Advisory result — no deployment approval.</strong><br>Real camera specifications. Fictional installation, timing assumptions, test records and costs. Voltage excluded.</div>
  <p class="small">Review context — current inventory part (not engineering-modeled). Candidate evaluated against the fixed synthetic installation. No approval workflow or hardware control.</p>
  <div class="row" style="margin-top:18px">
    <label>Proposed substitute<select aria-label="Proposed substitute" data-role="substitute"></select></label>
    <label>Synthetic fast-line requirement (fps)<input aria-label="Synthetic fast-line requirement" data-role="fps" value="45" inputmode="numeric" size="8"></label>
    <button data-role="review">Review substitution</button>
  </div>
  <div class="row" style="margin-top:14px">
    <label>Declared ISP (synthetic mode)<select aria-label="Declared ISP" data-role="isp"><option value="false">false</option><option value="true">true</option><option value="unknown">unknown</option></select></label>
    <button class="secondary" data-role="save">Save declared mode</button>
    <button class="secondary" data-role="compare">Check consumed inputs</button>
  </div>
  <p class="small" data-role="assumption">Request-local synthetic assumption; not a maintained project requirement.</p><p class="small" data-role="operation" aria-live="polite"></p><p class="error" data-role="error" role="alert"></p>
  <div class="row" style="margin-top:18px"><label>Preserved assessments<select aria-label="Preserved assessments" data-role="history"></select></label><button class="secondary" data-role="load">Open historical assessment</button></div>
  <div class="result" data-role="result" hidden></div>
  </section>`;
  mountedPanels.set(target, {identity, node: target.firstElementChild});
  const $ = role => target.querySelector('[data-role="'+role+'"]');
  const esc = value => {const n=document.createElement('span');n.textContent=String(value ?? 'unknown');return n.innerHTML;};
  const number = v => v && v.$rational ? v.$rational.join('/') : (v === null || v === undefined ? 'unknown' : String(v));
  const text = (role,value) => {$(role).textContent=value;};
  const get = async path => (await api.get(base+path)).data;
  const post = async (path,body) => (await api.post(base+path,body)).data;
  async function action(fn) {
    text('error',''); target.querySelectorAll('button').forEach(b=>b.disabled=true);
    try {await fn();} catch(e) {const r=e.response?.data;text('error',r ? JSON.stringify(r) : String(e));text('operation','No successful assessment is implied by this error.');}
    finally {target.querySelectorAll('button').forEach(b=>b.disabled=false);}
  }
  async function refreshHistory() {
    const rows=await get('assessments/?current='+encodeURIComponent(current));
    $('history').replaceChildren(...rows.map(r=>{const o=document.createElement('option');o.value=r.assessment_id;o.textContent=r.created_utc+' · '+r.engineering_status+' · '+r.assessment_id.slice(0,8);return o;}));
    if(assessment)$('history').value=assessment.assessment_id;
  }
  function render(s) {
    assessment=s;sessionStorage.setItem(selectionKey,s.assessment_id);const q=s.questions?.result;const ev=s.evaluations || [];
    const units={frame_rate:'fps',resolution:'mm/px',throughput:'MB/s',power:'W',timing:'mm'};
    const rows=ev.flatMap(e=>e.constraints.map(c=>`<tr><td>${esc(e.variant_id)}</td><td>${esc(c.constraint)}${units[c.constraint]?' ('+units[c.constraint]+')':''}</td><td>${esc(c.status)}</td><td>${esc(number(c.value))}</td><td>${esc(c.comparison)} ${esc(number(c.limit))}</td></tr>`)).join('');
    const policies=q?.analysis_status==='supported'?(q.policies||[]).map(p=>`<p><strong>${esc(p.policy)}:</strong> applicable guaranteed integration jitter ≤ <strong>${esc(number(p.threshold_ms))} ms</strong>. Conditional mathematical bound; a finite sample is not a guarantee.</p>`).join(''):'';
    const conditional=q?.analysis_status==='blocked'?'An established blocker prevents jitter evidence alone from making this candidate suitable.':q?.analysis_status==='unsupported'?'No supported jitter-only sufficiency claim for these inputs.':'';
    $('result').hidden=false;
    $('result').innerHTML=`<span class="badge ${s.blockers?.length?'bad':''}">${esc(s.engineering_status)}</span><span class="badge" data-role="freshness">Comparison pending</span>
      <p class="small">Review context — current inventory part (not engineering-modeled): ${esc(s.snapshot.current_part.name)}. Candidate: ${esc(s.snapshot.substitute_part.name)}; evaluated against the fixed synthetic installation.</p><p class="small">Inventory declaration matches configured source binding. This does not authenticate the physical device.</p><p class="small">Assessment ${esc(s.assessment_id)} · ${esc(s.created_utc)}</p>
      <p data-role="changes" class="small"></p><h3>Selected-camera assessment</h3><table><thead><tr><th>Variant</th><th>Constraint</th><th>Status</th><th>Value</th><th>Requirement</th></tr></thead><tbody>${rows}</tbody></table>
      <h3>Evidence status and established failures</h3><p>${s.counts ? Object.entries(s.counts).map(([k,v])=>esc(v)+" "+esc(k.replaceAll("_"," "))).join(" · ") : "Historical summary: original evidence classifications retained; no new counts inferred."}</p><p>${(s.reasons||[]).map(r=>esc(r.reason_class)+": "+esc((r.missing_premises||[]).join(", "))+" — "+esc(r.affected_source_rows.join(", "))).join("<br>")}</p><details><summary>Exact unknowns and evidence classifications</summary><pre>${esc(JSON.stringify({unknowns:s.unknowns,evidence:s.evidence,legacy_holds:s.evidence_holds},null,2))}</pre></details><h3>Evidence that could change the decision</h3><div class="question">${policies || '<p>'+esc(conditional || 'No supported evidence question is available in this result.')+'</p>'}<p class="small">Voltage and omitted real-world physics remain outside this result. No manufacturer timing guarantee is presumed.</p></div>
      <details><summary>Applicability, holds and unresolved evidence</summary><pre>${esc(JSON.stringify(s.applicability,null,2))}</pre></details>
      <details><summary>Source provenance and mapped inputs</summary><p class="small">Manufacturer capture, synthetic requirement and fictional test provenance remain distinct.</p><pre>${esc(JSON.stringify({mapping:s.mapping_trace,source_trace:s.source_trace},null,2))}</pre></details>
      <details><summary>Engine explanation (retained text)</summary><pre>${esc(q?.explanation || s.failure || 'Unavailable')}</pre></details>
      <p class="small">Recorded manifest SHA-256: ${esc(s.manifest_sha256)}. Applicable verifier: ${esc(JSON.stringify(s.verification_compatibility))}</p><button class="secondary" data-role="export">Export assessment records</button> <button class="secondary" data-role="verify-engine">Reproduce engine output</button> <button class="secondary" data-role="verify-decision">Verify recorded decision</button><p class="small" data-role="verification" aria-live="polite">No verification run in this view. In-host verification uses the bundled verifier with approved external-to-assessment runtime pins. A separately distributed CLI performs the same bounded verification outside InvenTree. Agreement with records and pinned software is not manufacturer truth or physical authentication.</p>`;
    for(const level of ['engine','decision']) $('verify-'+level).onclick=()=>action(async()=>{const r=await post('assessments/'+s.assessment_id+'/verify/',{level});text('verification','Historical verification: '+r.historical_verification.status+' · verified assurance '+(r.assurance_contract||'none')+' · assessment format '+(r.assessment_format_version||'unavailable')+' · executing verifier '+(r.historical_verification.executing_verifier_version||'unavailable')+' · dispatcher '+r.verifier_software_version+' · Recipient requirement: '+r.recipient_requirement.contract+' · Acceptance: '+r.acceptance.status+' ('+r.acceptance.code+') · Receipt saved: '+r.receipt_saved+' · Not deployment approval.');});
    labelAssumption(true);
    $('export').onclick=()=>action(async()=>{const r=await api.get(base+'assessments/'+s.assessment_id+'/export/',{responseType:'blob'});const u=URL.createObjectURL(new Blob([r.data],{type:'application/zip'}));const a=document.createElement('a');a.href=u;a.download='higgs-assessment-'+s.assessment_id+'.zip';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);});
  }
  function labelAssumption(restored=false) {
    if(!assessment)return;const saved=assessment.snapshot.requirements.fast_required_fps;
    text('assumption',$('fps').value===String(saved) ? 'Saved assessment assumption: '+saved+' fps'+(restored?' — restored from this assessment.':'.') : 'Draft / what-if assumption: '+$('fps').value+' fps; saved assessment assumption: '+saved+' fps. Not a maintained project requirement.');
  }
  $('fps').oninput=()=>labelAssumption();
  async function compare() {
    if(!assessment)return;
    let c;
    try {c=await get('assessments/'+assessment.assessment_id+'/compare/?fast_required_fps='+encodeURIComponent($('fps').value));}
    catch(e) {if(e.response?.data?.state==='INVALID_COMPARISON_INPUT'){text('freshness','INVALID_COMPARISON_INPUT');$('freshness').className='badge warn';text('changes','No current/stale verdict for this invalid draft assumption.');}throw e;}
    text('freshness',c.state);$('freshness').className='badge '+(c.state.startsWith('STALE')?'warn':'');
    text('changes',c.changes?.length ? c.changes.map(x=>x.change_class+' · '+x.field+': '+JSON.stringify(x.before)+' → '+JSON.stringify(x.after)).join(' | ') : c.message || 'Consumed inputs match at this check. Remote source content and physical conditions were not rechecked.');
  }
  $('review').onclick=()=>action(async()=>{text('operation','Running isolated analysis…');const s=await post('assessments/',{current_part:current,substitute_part:Number($('substitute').value),fast_required_fps:$('fps').value});render(s);labelAssumption();await compare();await refreshHistory();text('operation','Assessment preserved. Engineering status comes from structured results, not process exit alone.');});
  $('save').onclick=()=>action(async()=>{await post('mode/',{part_id:Number($('substitute').value),isp_enabled:$('isp').value});await compare();text('operation','Operating declaration saved. No camera setting or hardware changed.');});
  $('compare').onclick=()=>action(compare);
  $('load').onclick=()=>action(async()=>{const s=await get('assessments/'+$('history').value+'/');$('fps').value=s.snapshot.requirements.fast_required_fps;render(s);await compare();});
  $('substitute').onchange=()=>{$('isp').value=options.find(o=>o.part_id===Number($('substitute').value))?.isp_enabled || 'unknown';};
  action(async()=>{const result=await get('options/?current='+encodeURIComponent(current));options=result.options;$('substitute').replaceChildren(...options.map(o=>{const el=document.createElement('option');el.value=o.part_id;el.textContent=o.manufacturer+' · '+o.mpn;return el;}));const flir=options.find(o=>o.mpn==='BFS-U3-51S5M');if(flir)$('substitute').value=flir.part_id;$('substitute').onchange();await refreshHistory();const saved=sessionStorage.getItem(selectionKey);if(saved){const prior=await get('assessments/'+encodeURIComponent(saved)+'/');$('fps').value=prior.snapshot.requirements.fast_required_fps;render(prior);await compare();}text('operation','Inventory declaration matches configured source binding for accepted assessments. No physical unit is authenticated; free-text notes do not enforce conditions.');});
}
