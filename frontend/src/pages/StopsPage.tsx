import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CATEGORY_OPTIONS, CATEGORY_LABEL, Category } from "../categories";
type S = { id: number; route_id: number; seq: number; name: string; weight_kg: number; volume_l: number; category: Category };
type R = { id: number; name: string };
export default function StopsPage() {
  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [rows, setRows] = useState<S[]>([]);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  useEffect(() => {
    if (rid === "") return;
    setErr("");
    api<S[]>(`/stops?route_id=${rid}`).then(setRows);
  }, [rid]);
  async function changeCategory(s: S, category: Category) {
    setSavingId(s.id); setErr("");
    try {
      const updated = await api<S>(`/stops/${s.id}`, { method: "PATCH", body: JSON.stringify({ category }) });
      setRows(rs => rs.map(r => r.id === updated.id ? updated : r));
    } catch (e) { setErr(`「${s.name}」品类更新失败：${e instanceof Error ? e.message : String(e)}`); }
    finally { setSavingId(null); }
  }
  return (<>
    <h2>订户点</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <span className="hint">品类：普通可与任意品类同袋；<b className="cat-printed">印刷</b> 与 <b className="cat-liquid">液体</b> 不得同袋</span>
    </div>
    {err && <div className="err">{err}</div>}
    <div className="route-strip">
      {rows.map(s => (
        <div className={`stop-chip stop-chip--${s.category}`} key={s.id}>
          <span className="seq">#{s.seq}</span>
          <strong>{s.name}</strong>
          <span className="mono">{s.weight_kg}kg · {s.volume_l}L</span>
          <span className={`cat-tag cat-tag--${s.category}`}>{CATEGORY_LABEL[s.category]}</span>
          <select
            className="cat-select"
            value={s.category}
            disabled={savingId === s.id}
            onChange={e => changeCategory(s, e.target.value as Category)}
          >
            {CATEGORY_OPTIONS.map(c => <option key={c} value={c}>{CATEGORY_LABEL[c]}</option>)}
          </select>
        </div>
      ))}
    </div>
  </>);
}
