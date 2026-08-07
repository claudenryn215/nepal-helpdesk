interface Env {
  DB: D1Database;
}

interface CommentRow {
  id: number;
  parent_id: number | null;
  name: string;
  body: string;
  created_at: string;
  upvotes: number;
  downvotes: number;
}

const MAX_DEPTH = 5;

async function parentDepth(env: Env, commentId: number, postId: string): Promise<number | null> {
  let depth = 0;
  let current = commentId;
  for (let i = 0; i <= MAX_DEPTH; i++) {
    const row = await env.DB.prepare(
      'SELECT parent_id FROM comments WHERE id = ? AND post_id = ? AND approved = 1',
    )
      .bind(current, postId)
      .first<{ parent_id: number | null }>();
    if (!row) return null;
    if (row.parent_id === null) return depth;
    current = row.parent_id;
    depth++;
  }
  return null;
}

export const onRequest: PagesFunction<Env> = async ({ params, request, env }) => {
  const postId = String(params.id);

  if (request.method === 'GET') {
    const { results } = await env.DB.prepare(
      `SELECT id, parent_id, name, body, created_at, upvotes, downvotes
       FROM comments
       WHERE post_id = ? AND approved = 1
       ORDER BY (upvotes - downvotes) DESC, created_at ASC`,
    )
      .bind(postId)
      .all<CommentRow>();
    return Response.json({ postId, comments: results ?? [] });
  }

  if (request.method === 'POST') {
    let payload: { name?: unknown; body?: unknown; website?: unknown; parent_id?: unknown };
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

    let parentId: number | null = null;
    if (payload.parent_id !== undefined && payload.parent_id !== null) {
      const raw = Number(payload.parent_id);
      if (!Number.isInteger(raw) || raw <= 0) {
        return Response.json({ error: 'invalid parent' }, { status: 400 });
      }
      if ((await parentDepth(env, raw, postId)) === null) {
        return Response.json({ error: 'invalid parent' }, { status: 400 });
      }
      parentId = raw;
    }

    const createdAt = new Date().toISOString();
    const result = await env.DB.prepare(
      'INSERT INTO comments (post_id, parent_id, name, body, approved, created_at) VALUES (?, ?, ?, ?, 0, ?) RETURNING id',
    )
      .bind(postId, parentId, name, body, createdAt)
      .first<{ id: number }>();

    return Response.json({ id: result?.id ?? 0, pending: true });
  }

  return Response.json({ error: 'method not allowed' }, { status: 405 });
};
