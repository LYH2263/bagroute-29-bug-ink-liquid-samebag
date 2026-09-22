import { useEffect, useState } from "react";
import { api } from "../api/client";
import CategoryTag from "../components/CategoryTag";
type Rj = { id: number; route_id: number; stop_name: string; reason: string; category: string; created_at: string };
export default function RejectsPage() {
  const [rows, setRows] = useState<Rj[]>([]);
  useEffect(() => { api<Rj[]>("/rejects").then(setRows); }, []);
  return (<>
    <h2>拒收</h2>
    <table className="table"><thead><tr><th>时间</th><th>路线</th><th>品类</th><th>订户</th><th>原因</th></tr></thead>
    <tbody>{rows.map(r => <tr key={r.id}><td className="mono">{new Date(r.created_at).toLocaleString()}</td><td>{r.route_id}</td>
      <td><CategoryTag category={r.category} /></td><td>{r.stop_name}</td><td>{r.reason}</td></tr>)}
      {!rows.length && <tr><td colSpan={5}>暂无拒收</td></tr>}
    </tbody></table>
  </>);
}
