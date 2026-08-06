interface Env {
  DB: D1Database;
}

export const onRequest: PagesFunction<Env> = async ({ params, request, env }) => {
  const postId = String(params.id);
  const url = new URL(request.url);
  const isBot =
    /bot|crawl|spider|slurp|facebookexternalhit|whatsapp|preview/i.test(
      request.headers.get('user-agent') ?? '',
    ) || url.searchParams.has('bot');

  if (request.method === 'GET') {
    const row = await env.DB.prepare('SELECT count FROM views WHERE post_id = ?')
      .bind(postId)
      .first<{ count: number }>();
    return Response.json({ postId, count: row?.count ?? 0 });
  }

  if (request.method === 'POST') {
    if (isBot) {
      const row = await env.DB.prepare('SELECT count FROM views WHERE post_id = ?')
        .bind(postId)
        .first<{ count: number }>();
      return Response.json({ postId, count: row?.count ?? 0 });
    }
    const result = await env.DB.prepare(
      'INSERT INTO views (post_id, count) VALUES (?, 1) ON CONFLICT(post_id) DO UPDATE SET count = count + 1 RETURNING count',
    )
      .bind(postId)
      .first<{ count: number }>();
    return Response.json({ postId, count: result?.count ?? 1 });
  }

  return Response.json({ error: 'method not allowed' }, { status: 405 });
};
