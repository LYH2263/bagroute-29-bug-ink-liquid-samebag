import { catLabel } from "../categories";

export default function CategoryTag({ category }: { category?: string }) {
  const c = category ?? "normal";
  return <span className={`cat-tag cat-tag--${c}`}>{catLabel(c)}</span>;
}
