import socket
import threading


SERVER_KEY_REQUEST= '107 KEY REQUEST\a\b'.encode('utf-8')
SERVER_LOGIN_FAILED= '300 LOGIN FAILED\a\b'.encode("utf-8")
SERVER_OK='200 OK\a\b'.encode("utf-8")
SERVER_MOVE	= '102 MOVE\a\b'.encode('utf-8')	
SERVER_TURN_LEFT=	'103 TURN LEFT\a\b'.encode('utf-8')	
SERVER_TURN_RIGHT=	'104 TURN RIGHT\a\b'.encode('utf-8')	
SERVER_PICK_UP=	'105 GET MESSAGE\a\b'.encode('utf-8')
SERVER_LOGOUT=	'106 LOGOUT\a\b'.encode('utf-8')
SERVER_KEY_OUT_OF_RANGE_ERROR='303 KEY OUT OF RANGE\a\b'.encode('utf-8')
SERVER_SYNTAX_ERROR=	'301 SYNTAX ERROR\a\b'.encode('utf-8')
UNINICIALIZED = -1
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3
TARGET_POS=[0,0]


def EncapsulateMessage(data):
    data = str(data)
    data += '\a\b'
    data = data.encode('utf-8')
    return data


def ascii(username):
    if username.endswith('\a\b'):  # pokud řetězec končí sekvencí \a\b
        username = username[:-2]  # odebrat poslední dva znaky
    ascii = [ord(c) for c in username]  # převést řetězec na seznam ASCII hodnot
    return sum(ascii) 

def str_to_int(s):
    if s.endswith('\a\b'):
        s = s[:-2]
    return int(s)


def syntax_check(input_str):
    # Odstranění \a\b na konci řetězce
    if input_str.endswith('\a\b'):
        input_str=input_str[:-2]
    # Kontrola, zda se v řetězci nevyskytují znaky \a\b
    if '\a\b' in input_str:
        return False
    else:
        return True
    
def hash(id,username):
    sum=ascii(username)
    if id==0:
          hash=((sum*1000)%65536)+23019
    if id==1:
          hash=((sum*1000)%65536)+32037
    if id==2:
          hash=((sum*1000)%65536)+18789
    if id==3:
          hash=((sum*1000)%65536)+16443
    if id==4:
          hash=((sum*1000)%65536)+18189
    hash=EncapsulateMessage(hash)
    return hash
    
def compareHashes(username,key,id):
    sum=ascii(username)
    hash=sum*1000%65536
    if id==0:
        key += 65536 - 32037
        key %= 65536
    if id==1:
        key += 65536 - 29295
        key %= 65536
    if id==2:
        key += 65536 -13603
        key %= 65536
    if id==3:
        key += 65536 - 29533
        key %= 65536
    if id==4:
        key += 65536 - 21952
        key %= 65536
    if hash==key:
         return True
    else:
         return False
          
def read_from_socket(client_socket):
    buffer = ""  
    messages = []  
    data=""
    while True:

        try:
            data = client_socket.recv(1024)  
        except socket.timeout:
            print("TIMEOUT")
            client_socket.close()
            break

        if not data:
            break  # odpojení ze socketu

        buffer += data.decode()  # připojení nově přijatých dat ke zbytku nekompletní zprávy

        while True:
            index = buffer.find("\a\b")  # hledání ukončovací sekvence

            if index == -1:
                break  # ukončovací sekvence nenalezena

            message = buffer[:index]  # kompletní zpráva od začátku bufferu do indexu ukončovací sekvence
            buffer = buffer[index + 2:]  # zbývající nekompletní zpráva

            messages.append(message)  # přidání kompletní zprávy do seznamu zpráv

        # zkontrolujeme, zda máme nějaké nekompletní zprávy v bufferu
        while len(buffer) > 0:
            try:
                data = client_socket.recv(1024)  # přečtení dat ze socketu
            except socket.timeout:
                print("TIMEOUT")
                client_socket.close()
                break
            if not data:
                break  # odpojení ze socketu

            buffer += data.decode()  # připojení nově přijatých dat ke zbytku nekompletní zprávy

            # pokud jsme dostali kompletní zprávu, přidáme ji do seznamu
            index = buffer.find("\a\b")
            if index != -1:
                message = buffer[:index]  # kompletní zpráva od začátku bufferu do indexu ukončovací sekvence
                buffer = buffer[index + 2:]  # zbývající nekompletní zpráva
                messages.append(message)
                # pokud jsme získali kompletní zprávu, můžeme ukončit vnořený while cyklus

        if len(messages) > 0:
            break  # pokud máme alespoň jednu kompletní zprávu, ukončíme cyklus

    return messages

def autentication(client_socket, client_address):
   
    messages=read_from_socket(client_socket)
    list_lenght=len(messages)
    i=0
    username=messages[i]
    i=i+1
    if len(username) <= 20 and syntax_check(username)==True:  
        client_socket.send(SERVER_KEY_REQUEST)
        messages,i, list_lenght, id = get_next_message( messages, i, list_lenght, client_socket)
        
        if len(id) <= 5:
            id= str_to_int(id)
            if id<5 and id>=0:
                client_socket.send(hash(id,username))
                messages,i, list_lenght, key = get_next_message( messages, i, list_lenght, client_socket)
                
                if len(key)<=7:
                    key=str_to_int(key)
                    if compareHashes(username,key,id)==True:
                        client_socket.send(SERVER_OK)
                        if len(messages)==1:
                            return True #do listu seznamu předáme proměnnou i která urcuje pozici jeěte nepřečtené zprávy
                        else:
                            messages.append(str(i))
                            return messages
                    else:
                        client_socket.send(SERVER_LOGIN_FAILED)
                        client_socket.close()
                    
                        return False
                else:
                    client_socket.send(SERVER_LOGIN_FAILED)  
                    client_socket.close()
                    return False
            else:
                client_socket.send(SERVER_KEY_OUT_OF_RANGE_ERROR)
                client_socket.close()
                return False
                
        else:
            client_socket.send(SERVER_LOGIN_FAILED) 
            client_socket.close()
            return False         
    else:
        client_socket.send(SERVER_SYNTAX_ERROR)
        client_socket.close()
        return False

def handle_client(client_socket, client_address):
        
        messages=autentication(client_socket,client_address)
        if messages==False:
            return False
        navigate_robot(client_socket, messages)
        client_socket.close()
def get_next_message(messages,i,list_lenght,client_socket):

    if i<list_lenght and messages!=True:
        message=messages[i]
        i=i+1
    else:
        messages=read_from_socket(client_socket)
        list_lenght=len(messages)
        i=0
        message=messages[i]
        i=i+1
    return messages, i, list_lenght, message
       

def parse_position(message):
    
    if message.endswith('\a\b'):  # pokud řetězec končí sekvencí \a\b
        
        message = message[:-2]
    parts = message.split(' ')
    x = int(parts[1])
    y = int(parts[2])  # odebereme poslední \a\b z řetězce
    current_pos = [x, y]
    return current_pos


def get_direction(current_pos, previous_pos):
    x_diff = current_pos[0] - previous_pos[0]
    y_diff = current_pos[1] - previous_pos[1]

    if x_diff > 0:
        return RIGHT
    elif x_diff < 0:
        return LEFT
    elif y_diff > 0:
        return UP
    elif y_diff < 0:
        return DOWN
    else:
        return UNINICIALIZED  # Robot se nepohnul


def navigate_robot(client_socket,messages):
  
    crush=0
    i=0
    list_lenght=0
    if messages!=True:
        list_lenght=len(messages)
        i=int(messages[list_lenght-1])
        messages.pop(-1)
        
    

    client_socket.send(SERVER_MOVE)
    if i<list_lenght and messages!=True:
        message=messages[i]
        i=i+1
    else:
        messages=read_from_socket(client_socket)
        list_lenght=len(messages)
        i=0
        message=messages[i]
        i=i+1
    
    current_pos=parse_position(message)
    previous_pos=current_pos
    client_socket.send(SERVER_MOVE)
    if i<len(messages):
        message=messages[i]
        i=i+1
    else:
        messages=read_from_socket(client_socket)
        list_lenght=len(messages)
        i=0
        message=messages[i]
        i=i+1
   
    current_pos=parse_position(message)
    direction=get_direction(current_pos,previous_pos)
    if direction==UNINICIALIZED:
        crush=+1
                
        

        client_socket.send(SERVER_TURN_LEFT)
        client_socket.recv(1024)
        client_socket.send(SERVER_MOVE)
        client_socket.recv(1024)
        client_socket.send(SERVER_TURN_RIGHT)
        client_socket.recv(1024)
        client_socket.send(SERVER_MOVE)
        client_socket.recv(1024)
        client_socket.send(SERVER_MOVE)
        client_socket.recv(1024)
        client_socket.send(SERVER_TURN_RIGHT)
        messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
        previous_pos=parse_position(message)
        client_socket.send(SERVER_MOVE)
        messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
        current_pos=parse_position(message)
        direction=get_direction(current_pos,previous_pos)
        if current_pos==TARGET_POS:
            client_socket.send(SERVER_PICK_UP)
            client_socket.recv(1024)
            client_socket.close()
            return


    while True:
        
        if current_pos[0] < TARGET_POS[0]:
            if direction==RIGHT:
                client_socket.send(SERVER_MOVE)
            if direction==UP:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==DOWN:
                client_socket.send(SERVER_TURN_LEFT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==LEFT:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            direction=RIGHT

        elif current_pos[0] > TARGET_POS[0]:
            if direction==LEFT:
                client_socket.send(SERVER_MOVE)
            if direction==UP:
                client_socket.send(SERVER_TURN_LEFT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==RIGHT:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==DOWN:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)

            direction=LEFT

        elif current_pos[1] < TARGET_POS[1]:
            if direction==UP:
                client_socket.send(SERVER_MOVE)
            if direction==RIGHT:
                client_socket.send(SERVER_TURN_LEFT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==DOWN:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==LEFT:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            direction=UP

        elif current_pos[1] > TARGET_POS[1]:            
            if direction==DOWN:
                client_socket.send(SERVER_MOVE)
            if direction==UP:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            if direction==RIGHT:
                client_socket.send(SERVER_TURN_RIGHT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)

            if direction==LEFT:
                client_socket.send(SERVER_TURN_LEFT)
                messages,i, list_lenght, message = get_next_message( messages, i, list_lenght, client_socket)
                client_socket.send(SERVER_MOVE)
            direction=DOWN
        else:
            client_socket.send(SERVER_PICK_UP)
            client_socket.recv(1024)
            direction= UNINICIALIZED
        
        if direction!=UNINICIALIZED:
            
            
            messages=read_from_socket(client_socket)
            list_lenght=len(messages)
            i=0
            message=messages[i]
            i=i+1
            print(message)
            previous_pos=current_pos
            current_pos=parse_position(message)
            if current_pos==previous_pos:
                crush=+1
                if crush>=20:
                    client_socket.close()
                    break
                
                client_socket.send(SERVER_TURN_LEFT)
                client_socket.recv(1024)
                client_socket.send(SERVER_MOVE)
                client_socket.recv(1024)
                client_socket.send(SERVER_TURN_RIGHT)
                client_socket.recv(1024)
                client_socket.send(SERVER_MOVE)
                client_socket.recv(1024)
                client_socket.send(SERVER_MOVE)
                client_socket.recv(1024)
                client_socket.send(SERVER_TURN_RIGHT)
                client_socket.recv(1024)
                client_socket.send(SERVER_MOVE)
                client_socket.recv(1024)
                client_socket.send(SERVER_TURN_LEFT)
                messages=read_from_socket(client_socket)
                list_lenght=len(messages)
                i=0
                message=messages[i]
                i=i+1
            

                current_pos=parse_position(message)

           
        else:
            
            client_socket.send(SERVER_LOGOUT)

            break

def main():

    # vytvori tcp server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    server_socket.bind(('localhost', 3999))
    server_socket.listen(10)

    while True:
        
        
        client_socket, client_address = server_socket.accept()
        
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
        client_socket.settimeout(1)
        print('waiting for a connection')
        
        



if __name__ == "__main__":
    main()