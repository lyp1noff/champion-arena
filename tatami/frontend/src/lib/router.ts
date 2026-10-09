export function useRouteParams(): Record<string, string> {
  const path = window.location.pathname.replace(/\/+$/, "");
  let match = path.match(/^\/admin\/tatami\/([^/]+)\/match\/([^/]+)$/);
  if (match) return { id: decodeURIComponent(match[1]), match_id: decodeURIComponent(match[2]) };
  match = path.match(/^\/admin\/tatami\/([^/]+)$/);
  if (match) return { id: decodeURIComponent(match[1]) };
  return {};
}

export function useAppRouter() {
  return { push(path: string) { window.location.assign(path); } };
}
