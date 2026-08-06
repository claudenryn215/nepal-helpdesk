interface Env {
  DB: D1Database;
}

export const onRequest: PagesFunction<Env> = async ({ request, env }) => {
  if (request.method !== 'GET') {
    return Response.json({ error: 'method not allowed' }, { status: 405 });
  }
  const url = new URL(request.url);
  const ids = (url.searchParams.get('ids') ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, 60);
  if (ids.length === 0) {
    return Response.json({ counts: {} });
  }

  const placeholders = ids.map(() => '?').join(',');
  const { results } = await env.DB.prepare(
    `SELECT post_id, COUNT(*) AS total FROM comments WHERE post_id IN (${placeholders}) AND approved = 1 GROUP BY post_id`,
  )
    .bind(...ids)
    .all<{ post_id: string; total: number }>();

  const counts: Record<string, number> = {};
  for (const row of results ?? []) {
    counts[row.post_id] = row.total;
  }
  return Response.json({ counts });
};
