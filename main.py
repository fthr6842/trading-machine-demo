from TTBHelp import *
import threading, time
import pandas as pd

class TTBProcess(TTBModule):
    def SHOWQUOTEDATA(self,obj):
        global price_temp
        print("Symbol:{}, BidPs:{}, BidPv:{}, AskPs:{}, AskPv:{}, T:{}, P:{}, V:{}, Volume:{}".format(obj['Symbol'],obj['BidPs'],obj['BidPv'],obj['AskPs'],obj['AskPv'],obj['TickTime'],obj['Price'],obj['Qty'],obj['Volume']))
        price_temp = obj["Price"].replace(",", "") #string

def putOrd(commodity = "TXFF4", Price = "21014", Qty = "1", side = "buy"): #下單
    
    if side == "buy": side = "1"
    elif side == "sell": side = "2"
    else:
        print("Err")
        return 0
    
    putOrd = {
        "Symbol1": commodity,
        "Price": Price,
        "TimeInForce":"2",
        "Side1": side,
        "OrderType": "2",
        "OrderQty": Qty,
        "DayTrade":"0",
        "Symbol2":"",
        "Side2":"",
        "PositionEffect": "4",
    }
    
    msgDic = ttbModule.NEWORDER(putOrd)
    print("=" * 10)
    print(msgDic)
    print(side, ", Price: ", Price, ", Qty: ", Qty)
    print("time: ", time.ctime())
    print("=" * 10)
    return 0

def canlOrd (No): #刪單
    
    canlOrd = {"OrdNo": No}
    
    msgDic = ttbModule.CANCELORDER(canlOrd)
    print(msgDic)
    return 0

def ChangePrice (No, Price): #改價
    
    changePrice = {
        "OrdNo": No,
        "Price": Price
    }
    
    msgDic = ttbModule.REPLACEPRICE(changePrice)
    print(msgDic)
    return 0

def portion_report():
    msgDic = ttbModule.QUERYRESTOREFILLREPORT()
    #print(len(msgDic["Data"]))
    return len(msgDic["Data"])

def ord_report():
    msgDic = ttbModule.QUERYRESTOREREPORT()
    #print(len(msgDic["Data"]))
    return len(msgDic["Data"])

def RSI(data, window=14):
    # 計算每日收益
    data = pd.DataFrame({"Price": data})
    delta = data['Price'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)

    # 計算平均收益和平均損失
    avg_gain = gain.rolling(window=window, min_periods=1).mean() #min_periods: 計算所需的最小期間
    avg_loss = loss.rolling(window=window, min_periods=1).mean()

    rs = avg_gain / avg_loss # 計算RS
    rsi = 100 - (100 / (1 + rs)) # 計算RSI
    
    return round(rsi.iloc[-1], 2)


if __name__ == "__main__":
    ttbModule = TTBProcess('http://localhost:8080', 51141) #與主機連線
    
    target = "TXFF4" #監聽報價的對象
    price_temp = 0 # 初始化價格變數
    data = [] #只保留近100筆價格資料
    portion = 0 #倉位，預設為無倉位 (測試期間上限為5口)
    Ord = 0 #委託倉位，預設為無倉位
    T = 3600 #預計運行1小時 (3600秒)
    
    thread_1 = threading.Thread(target=ttbModule.QUOTEDATA, args=(target,))
    thread_1.start()
    
    #先建立20筆報價
    for i in range(0, 20):
        time.sleep(3) #預設間格為10秒
        data.append(float(price_temp)) #將最新價格加入資料集
    
    print('-' * 10)
    print("資料徵集結束")
    print('-' * 10)
    
    t0 = time.time() #下單系統開始時間
    while time.time() <= t0 + T :
        #time.sleep(1)
        data.append(float(price_temp)) #將最新價格加入資料集
        if len(data) < 100: data = data[1:] #若資料集多於100筆，則去掉第1筆
        
        portion, Ord = portion_report(), ord_report() #更新未平倉部位、委託部位
        
        rsi = RSI(data) #計算rsi值
        
        #回報當前RSI、時間、部位
        print("-" * 10)
        print("RSI: ", rsi)
        print("price: ", price_temp)
        print("time: ", time.ctime())
        print("Portion: ", portion, "; Order: ", Ord)
        print("-" * 10)
        
        if rsi > 80 and portion > 0: #超買，若有部位則賣出全部倉位，且不做空
            putOrd(commodity = target[0], Price = price_temp, Qty = portion, side = "sell")
            print("=" * 10)
            print(target[0],  ", sell, price: ", price_temp)
            print("time: ", time.ctime())
            print("=" * 10)
        elif rsi < 20 and portion < 5: #超賣，若無部位則買進，直到達到上限
            if Ord < 2: #若已委託單數低於2，則繼續委託
                putOrd(commodity = target[0], Price = price_temp, Qty = 1, side = "buy")
                print("=" * 10)
                print(target[0], ", buy, price:", price_temp)
                print("time: ", time.ctime())
                print("=" * 10)
            else: pass
        else: pass
        
        #查詢權益數
        msgDic = ttbModule.QUERYMARGIN()
        print('-' * 10)
        print("Balance: ", msgDic["Data"][0]["BALN"])
        print('-' * 10)
    
print("下單系統結束")
thread_1.join()
print("請手動終止報價系統") 
        
        
        