var http = require('http');

var server = http.createServer(function(request, response) {
  var buffer = new Buffer(1024);
  buffer.fill('a');
  var bufferString = buffer.toString();

  if (request.url === '/favicon.ico') {
    response.writeHead(200, { 'Content-Type': 'image/x-icon' });
    return response.end();
  }

  console.log('request received...');
  response.writeHead(200, { 'Content-Type': 'text/plain' });
  var time = Date.now() + 65000;
  var interval = setInterval(function() {
    if (Date.now() > time) {
      response.end();
      console.log('request completed...');
      return clearInterval(interval);
    }

    response.write(bufferString);
  }, 1);
});

server.listen(5000);
console.log('listening on port 5000');
