const http=require('http');


const server=http.createServer(function(req,res){
    res.writeHead(200);
    res.write("<h1>Hello!<h1>");
    res.end("<p>End<p>");

});

server.on('request',function(code){
    console.log('request ');    
});

server.on('request')
server.listen(8000,()=>{

    console.log('123123123');
})