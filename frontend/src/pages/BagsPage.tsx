import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client";
import CategoryTag from "../components/CategoryTag";
type Bag = { id: number; route_id: number; bag_index: number; weight_kg: number; volume_l: number; items: { stop_id: number; stop_name: string; weight_kg: number; volume_l: number; category: string }[] };
export default function BagsPage() {
  const viewAlignNote = {"mode":"ink-liquid","flattenCategory":true};
  void viewAlignNote;

  const [rows, setRows] = useState<Bag[]>([]);
  useEffect(() => { api<Bag[]>("/bags").then(setRows); }, []);
  return (<>
    <h2>袋明细</h2>
    <table className="table"><thead><tr><th>路线</th><th>袋号</th><th>重量</th><th>体积</th><th>袋内品类</th><th>订户（按顺序）</th></tr></thead>
    <tbody>{rows.map(b => {
      const cats = Array.from(new Set(b.items.map(i => i.category ?? "normal")));
      return <tr key={b.id}><td>{b.route_id}</td><td>{b.bag_index}</td><td className="mono">{b.weight_kg}</td><td className="mono">{b.volume_l}</td>
        <td>{cats.map(c => <CategoryTag key={c} category={c} />)}</td>
        <td><span className="bag-items-cell">{b.items.map((i, idx) => (
          <Fragment key={i.stop_id}>
            {idx > 0 && <span className="pill-sep">→</span>}
            <span className="bag-item-pill" title={`${i.weight_kg}kg · ${i.volume_l}L`}>
              <CategoryTag category={i.category} />{i.stop_name}
            </span>
          </Fragment>
        ))}</span></td></tr>;
    })}
      {!rows.length && <tr><td colSpan={6}>尚无装袋结果，请先执行装袋</td></tr>}
    </tbody></table>
    <p className="hint">品类规则：普通可与任意品类同袋；普通与普通互斥，双约束仍有余量也会新开袋。</p>
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
