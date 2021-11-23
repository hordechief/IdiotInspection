from http.server import HTTPServer,BaseHTTPRequestHandler
class Request(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)
        self.send_response(200)
        # 标识传递数据类型
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write('here we transfer data'.encode())
        # 下面的形式可以用来传html文件
        # with open('D:\\Python网络编程基础\\Python代码\\http.html','rb') as t:
        #     print('输出了')
        #     self.wfile.write(t.read())

def run():
    host='localhost'
    port=80
    server=HTTPServer((host,port),Request)
    server.serve_forever()
    
if __name__=='__main__':
    # print(Request.path)
    run()
