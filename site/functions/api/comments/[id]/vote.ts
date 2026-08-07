interface Env {
  DB: D1Database;
}

async function voterId(request: Request): Promise<string> {
  const raw = `${request.headers.get('cf-connecting-ip') ?? 'unknown'}|${
    request.headers.get('user-agent') ?? ''
  }`;
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(raw));
  return [...new Uint8Array(digest)]
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
    .slice(0, 24);
}

async function recount(env: Env, commentId: number): Promise<void> {
  await env.DB.prepare(
    `UPDATE comments SET
       upvotes = (SELECT COUNT(*) FROM comment_votes WHERE comment_id = ? AND direction = 1),
       downvotes = (SELECT COUNT(*) FROM comment_votes WHERE comment_id = ? AND direction = -1)
     WHERE id = ?`,
  )
    .bind(commentId, commentId, commentId)
    .run();
}

export const onRequest: PagesFunction<Env> = async ({ params, request, env }) => {
  if (request.method !== 'POST') {
    return Response.json({ error: 'method not allowed' }, { status: 405 });
  }

  const commentId = Number(params.id);
  if (!Number.isInteger(commentId) || commentId <= 0) {
    return Response.json({ error: 'invalid comment' }, { status: 400 });
  }

  let payload: { direction?: unknown };
  try {
    payload = await request.json();
  } catch {
    return Response.json({ error: 'invalid body' }, { status: 400 });
  }

  const direction = Number(payload.direction);
  if (![-1, 0, 1].includes(direction)) {
    return Response.json({ error: 'invalid direction' }, { status: 400 });
  }

  const comment = await env.DB.prepare('SELECT post_id FROM comments WHERE id = ? AND approved = 1')
    .bind(commentId)
    .first<{ post_id: string }>();
  if (!comment) {
    return Response.json({ error: 'comment not found' }, { status: 404 });
  }

  const voter = await voterId(request);

  if (direction === 0) {
    await env.DB.prepare('DELETE FROM comment_votes WHERE comment_id = ? AND voter = ?')
      .bind(commentId, voter)
      .run();
  } else {
    await env.DB.prepare(
      `INSERT INTO comment_votes (comment_id, voter, direction) VALUES (?, ?, ?)
       ON CONFLICT(comment_id, voter) DO UPDATE SET direction = excluded.direction`,
    )
      .bind(commentId, voter, direction)
      .run();
  }
  await recount(env, commentId);

  const row = await env.DB.prepare('SELECT upvotes, downvotes FROM comments WHERE id = ?')
    .bind(commentId)
    .first<{ upvotes: number; downvotes: number }>();

  const upvotes = row?.upvotes ?? 0;
  const downvotes = row?.downvotes ?? 0;
  return Response.json({ id: commentId, upvotes, downvotes, score: upvotes - downvotes, myVote: direction });
};
