// Query string that reproduces a search, so that the address bar can be shared.
export function searchParams(current, query, all) {
  const params = new URLSearchParams(current);
  if (query.trim() === "") {
    params.delete("q");
    params.delete("all");
  } else {
    params.set("q", query.trim());
    if (all) params.set("all", "1");
    else params.delete("all");
  }
  const text = params.toString();
  return text ? `?${text}` : "";
}
