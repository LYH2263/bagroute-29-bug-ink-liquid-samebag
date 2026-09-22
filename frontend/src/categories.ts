export type Category = "normal" | "printed" | "liquid";

export const CATEGORY_LABEL: Record<Category, string> = {
  normal: "普通",
  printed: "印刷",
  liquid: "液体",
};

export const CATEGORY_OPTIONS: Category[] = ["normal", "printed", "liquid"];

export function catLabel(c?: string): string {
  return CATEGORY_LABEL[(c as Category)] ?? "普通";
}
