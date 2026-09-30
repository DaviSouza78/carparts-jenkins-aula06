const http = require('node:http');
const { readFile } = require('node:fs/promises');
const path = require('node:path');

const orders = new Map();

function app(req, res) {
  const send = (status, body) => {
    res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify(body));
  };
  if (req.method === 'GET' && req.url === '/health') {
    return send(200, { status: 'ok', service: 'carparts-b2b-demo' });
  }
  if (req.method === 'GET' && req.url === '/api/orders') {
    return send(200, { orders: [...orders.values()] });
  }
  if (req.method === 'POST' && req.url === '/api/orders') {
    let raw = '';
    req.on('data', chunk => {
      raw += chunk;
      if (raw.length > 10000) req.destroy();
    });
    req.on('end', () => {
      try {
        const input = JSON.parse(raw);
        if (typeof input.part !== 'string' || !input.part.trim() || !Number.isInteger(input.quantity) || input.quantity < 1) {
          return send(400, { error: 'part e quantity inteiro positivo são obrigatórios' });
        }
        const order = { id: String(orders.size + 1), part: input.part.trim(), quantity: input.quantity };
        orders.set(order.id, order);
        return send(201, order);
      } catch {
        return send(400, { error: 'JSON inválido' });
      }
    });
    return;
  }
  if (req.method === 'GET' && (req.url === '/' || req.url === '/index.html')) {
    readFile(path.join(__dirname, 'public', 'index.html'))
      .then(file => { res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' }); res.end(file); })
      .catch(() => send(500, { error: 'front-end indisponível' }));
    return;
  }
  send(404, { error: 'não encontrado' });
}

if (require.main === module) {
  const port = Number(process.env.PORT || 3000);
  http.createServer(app).listen(port, '0.0.0.0');
}
module.exports = { app };
