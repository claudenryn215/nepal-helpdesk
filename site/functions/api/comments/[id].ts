interface Env {
  DB: D1Database;
}

interface CommentRow {
  id: number;
  name: string;
  body: string;
  created_at: string;
}

export const onRequest: PagesFunction<Env> = async ({ params, request, env }) => {
  const postId = String(params.id);

  if (request.method === 'GET') {
    const { results } = await env.DB.prepare(
      'SELECT id, name, body, created_at FROM comments WHERE post_id = ? AND approved = 1 ORDER BY created_at ASC',
    )
      .bind(postId)
      .all<CommentRow>();
    return Response.json({ postId, comments: results ?? [] });
  }

  if (request.method === 'POST') {
    let payload: { name?: unknown; body?: unknown; website?: unknown };
    try {
      payload = await request.json();
    } catch {
      return Response.json({ error: 'invalid body' }, { status: 400 });
    }

    const website = typeof payload.website === 'string' ? payload.website.trim() : '';
    if (website !== '') {
      return Response.json({ error: 'spam' }, { status: 400 });
    }

    const name = typeof payload.name === 'string' ? payload.name.trim().slice(0, 40) : '';
    const body = typeof payload.body === 'string' ? payload.body.trim().slice(0, 800) : '';
    if (name.length < 2 || body.length < 2) {
      return Response.json({ error: 'name and comment are required' }, { status: 400 });
    }

    const createdAt = new Date().toISOString();
    const result = await env.DB.prepare(
      'INSERT INTO comments (post_id, name, body, approved, created_at) VALUES (?, ?, ?, 0, ?) RETURNING id',
    )
      .bind(postId, name, body, createdAt)
      .first<{ id: number }>();

    return Response.json({ id: result?.id ?? 0, pending: true });
  }

  return Response.json({ error: 'method not allowed' }, { status: 405 });
};
