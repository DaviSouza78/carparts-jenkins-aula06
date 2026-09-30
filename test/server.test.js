const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const { app } = require('../src/server');

async function withServer(fn) {
  const server = http.createServer(app);
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try { await fn(`http://127.0.0.1:${server.address().port}`); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

test('health responde com serviço disponível', () => withServer(async base => {
  const response = await fetch(`${base}/health`);
  assert.equal(response.status, 200);
  assert.equal((await response.json()).status, 'ok');
}));

test('cria pedido válido e lista o pedido', () => withServer(async base => {
  const response = await fetch(`${base}/api/orders`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ part: 'Filtro', quantity: 2 }) });
  assert.equal(response.status, 201);
  const order = await response.json();
  assert.equal(order.part, 'Filtro');
  const list = await (await fetch(`${base}/api/orders`)).json();
  assert.ok(list.orders.some(item => item.id === order.id));
}));

test('rejeita quantidade inválida', () => withServer(async base => {
  const response = await fetch(`${base}/api/orders`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ part: 'Filtro', quantity: 0 }) });
  assert.equal(response.status, 400);
}));

test('rejeita JSON inválido', () => withServer(async base => {
  const response = await fetch(`${base}/api/orders`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: '{' });
  assert.equal(response.status, 400);
}));
