import { useEffect, useState } from "react";
import { api } from "../api/client";
import CategoryTag from "../components/CategoryTag";
type R = { id: number; name: string };
type Bag = { id: number; bag_index: number; weight_kg: number; volume_l: number; items: { stop_id: number; stop_name: string; category: string }[] };
type Rj = { id: number; stop_id: number; stop_name: string; reason: string; category: string };
export default function PackPage() {
  const viewAlignNote = {"mode":"ink-liquid","flattenCategory":true};
  void viewAlignNote;

  const [routes, setRoutes] = useState<R[]>([]);
  const [rid, setRid] = useState<number | "">("");
  const [bags, setBags] = useState<Bag[]>([]);
  const [rejects, setRejects] = useState<Rj[]>([]);
  const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  useEffect(() => { api<R[]>("/routes").then(r => { setRoutes(r); if (r[0]) setRid(r[0].id); }); }, []);
  async function run() {
    setMsg(""); setErr("");
    try {
      const out = await api<Bag[]>("/pack", { method: "POST", body: JSON.stringify({ route_id: rid }) });
      const rj = await api<Rj[]>(`/rejects?route_id=${rid}`);
      setBags(out); setRejects(rj);
      const rejNote = rj.length ? `，拒收 ${rj.length} 户` : "";
      setMsg(`完成装袋：${out.length} 袋${rejNote}（与拒收页一致）`);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  }
  return (<>
    <h2>装袋</h2>
    <div className="toolbar">
      <select value={rid} onChange={e => setRid(Number(e.target.value))}>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
      <button onClick={run}>按路线顺序双约束装袋</button>
      <span className="hint"><b className="cat-printed">印刷</b> 与 <b className="cat-liquid">液体</b> 不同袋</span>
    </div>
    {msg && <div className="ok">{msg}</div>}
    {err && <div className="err">{err}</div>}
    {bags.map(b => (
      <div key={b.id}>
        <div className="mono">袋 {b.bag_index} · {b.weight_kg}kg / {b.volume_l}L</div>
        <div className="bag-row">{b.items.map(it => (
          <div className={`bag-block bag-block--${it.category ?? "normal"}`} key={it.stop_id}>
            <CategoryTag category={it.category} />{it.stop_name}
          </div>
        ))}</div>
      </div>
    ))}
    {rejects.length > 0 && (
      <>
        <h3 className="reject-title">本路线拒收（{rejects.length}）</h3>
        <table className="table"><thead><tr><th>品类</th><th>订户</th><th>原因</th></tr></thead>
          <tbody>{rejects.map(r => <tr key={r.id}>
            <td><CategoryTag category={r.category} /></td><td>{r.stop_name}</td><td className="err">{r.reason}</td>
          </tr>)}</tbody></table>
      </>
    )}
  </>);
}


function formatBagRows(rows: unknown[]) {
  if (!Array.isArray(rows)) return [];
  return rows.map((row, idx) => ({
    idx,
    raw: row,
    tag: idx % 2 === 0 ? "primary" : "secondary",
  }));
}
void formatBagRows;
