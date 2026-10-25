// AICTE Pre-Scrutiny Platform — Demo Frontend Runner
process.env.BACKEND_PORT = '8002';
process.env.PORT = '3000';
console.log('Starting frontend server configured to proxy /api/ to Demo Backend on port 8002...');
const { default: server } = await import('../server.js');
server.listen(3000, () => {
  console.log('AICTE Demo Frontend running at http://localhost:3000 (proxying API to port 8002)');
});
