from machine import Pin
import gxgde0213b1
import G_FreeSans24pt7b
import font12
import font16
import font20
import font24
import network
import ubinascii
import urandom
import machine
from microWebSrv import MicroWebSrv

#initialize the epaper
reset = Pin(16, Pin.OUT)
dc = Pin(25, Pin.OUT)
busy = Pin(4, Pin.IN)
cs = Pin(5, Pin.OUT)
epd = gxgde0213b1.EPD(reset, dc, busy, cs)
epd.init()

#create the frame buffer and set proper screen rotation
fb_size = int(epd.width * epd.height / 8)
fb = bytearray(fb_size)
epd.clear_frame(fb)
epd.set_rotate(gxgde0213b1.ROTATE_90)

def start_ap_mode():
	ap = network.WLAN(network.AP_IF)
	ap.active(True)

	essid = 'ohsbadge-' + ubinascii.hexlify(network.WLAN().config('mac'),':').decode()
	password = str(urandom.getrandbits(30))
	ap.config(essid=essid)
	ap.config(authmode=3, password=password)
	ipaddr = ap.ifconfig()[0]

  
	epd.clear_frame(fb)
	epd.set_rotate(gxgde0213b1.ROTATE_270)
	epd.display_string_at(fb, 0, 0, "Welcome to OHS 2018!", font16, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 20, "ESSID = " + essid, font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 32, "PASSWORD = " + password, font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 44, "IP ADDR = " + ipaddr, font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 60, "Connect to badge AP to configure." , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 72, "Enter this URL in your browser:" , font12, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 84, "http://" + ipaddr + "/setup", font12, gxgde0213b1.COLORED)
	epd.display_frame(fb)

@MicroWebSrv.route('/setup')
def _httpHandlerTestGet(httpClient, httpResponse) :
	content = """\
	<!DOCTYPE html>
	<html lang=en>
        <head>
        	<meta charset="UTF-8" />
            <title>OHS Badge Configuration Page</title>
        </head>
        <body>
            <h1>Enter your name</h1>
            Client IP address = %s
            <br />
			<form action="/setup" method="post" accept-charset="ISO-8859-1">
				First name: <input type="text" name="firstname"><br />
				Last name: <input type="text" name="lastname"><br />
				<input type="submit" value="Submit">
			</form>
        </body>
    </html>
	""" % httpClient.GetIPAddr()
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )

@MicroWebSrv.route('/setup', 'POST')
def _httpHandlerTestPost(httpClient, httpResponse) :
	formData  = httpClient.ReadRequestPostedFormData()
	firstname = formData["firstname"]
	lastname  = formData["lastname"]
	content   = """\
	<!DOCTYPE html>
	<html lang=en>
		<head>
			<meta charset="UTF-8" />
            <title>OHS Badge Configuration Post</title>
        </head>
        <body>
            <h1>Name sent to badge</h1>
            Firstname = %s<br />
            Lastname = %s<br />
        </body>
    </html>
	""" % ( MicroWebSrv.HTMLEscape(firstname),
		    MicroWebSrv.HTMLEscape(lastname) )
	httpResponse.WriteResponseOk( headers		 = None,
								  contentType	 = "text/html",
								  contentCharset = "UTF-8",
								  content 		 = content )
	epd.clear_frame(fb)
	epd.display_string_at(fb, 0, 0, firstname, font24, gxgde0213b1.COLORED)
	epd.display_string_at(fb, 0, 24, lastname, font24, gxgde0213b1.COLORED)
	epd.display_frame(fb)
	#TODO save output to a file to be loaded on next boot
	goto_deepsleep()

def goto_deepsleep():
	#go to deepsleep wait for user to press the send button
	button = machine.TouchPad(machine.Pin(33))
	reading = button.read()
	button.config(int(2/3 * reading))
	button.callback(lambda t:print("Pressed"))
	machine.deepsleep()

def start_web_server():
	srv = MicroWebSrv(webPath='www/')
	srv.MaxWebSocketRecvLen     = 256
	srv.WebSocketThreaded		= False
	#srv.AcceptWebSocketCallback = _acceptWebSocketCallback
	srv.Start(threaded=False)

def start():
	#draw the screen TODO: make this dynamic based on the contents of file
	epd.G_display_string_at(fb,0,0,"OHS 2018",G_FreeSans24pt7b,1,gxgde0213b1.COLORED)
	#epd.display_string_at(fb, 0, 0, "OHS 2018", font24, gxgde0213b1.COLORED)
	#epd.display_string_at(fb, 0, 24, "TODO: Draw logo :P", font16, gxgde0213b1.COLORED)
	#epd.draw_custom_font_char(fb,50,50,1,'A'[0],G_FreeSans24pt7b,gxgde0213b1.COLORED)
	epd.display_frame(fb)

	if machine.wake_reason() == machine.TOUCHPAD_WAKE:
		#go into AP mode
		#TODO add support for detecting which button cause the wakeup
		start_ap_mode()
		start_web_server()
	else:
		goto_deepsleep()

