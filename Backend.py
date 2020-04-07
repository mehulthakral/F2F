from flask import Flask,jsonify,request,Response
import os
import requests
import price_suggestion as ps
import related_products as rp

app = Flask(__name__)

import Requirements as R

@app.route('/api/login', methods=['GET'])
def login():
    json = request.get_json()

    if(json["type"] == "consumer"):
        inp={"table":"CONSUMER","where":"CONSID ="+json["userid"]}
    else:
        inp={"table":"FARMER","where":"FAMRID ="+json["userid"]}
    send=requests.get('http://127.0.0.1:5000/api/check',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response("1",status=200,mimetype="application/text")
    else:
        return Response("0",status=204,mimetype="application/text")

@app.route('/api/deals/<num>', methods=['GET'])
def deals(num):

    inp={"table":"DEALS","columns":["*"],"where":"PRODID>0 ORDER BY DISCOUNT_PERCENT DESC LIMIT "+num}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)

    result = []
    for deal in data:
        send=requests.get('http://127.0.0.1:5000/api/product/'+str(deal[1]))
        res=send.content
        res=eval(res)
        res["UNIT_PRICE"]=deal[2]
        res["DISCOUNT_PERCENT"]=deal[3]
        result.append(res)

    return jsonify(result)

@app.route('/api/related/<prodid>', methods=['GET'])
def related_products(prodid):

    inp={"table":"PRODUCT","columns":["PRODTITLE"],"where":"PRODID = "+prodid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    rel = rp.related(data[0][0])

    result = []
    for prod in rel:
        inp={"table":"PRODUCT","columns":["PRODID"],"where":"PRODTITLE LIKE '"+prod+"%'"}
        send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
        ids=send.content
        ids=eval(ids)
        for pid in ids:
            send=requests.get('http://127.0.0.1:5000/api/product/'+str(pid[0]))
            res=send.content
            res=eval(res)
            del res["MAXQUANT"]
            del res["MINBUYQUANT"]
            result.append(res)

    return jsonify(result)

@app.route('/api/price', methods=['GET'])
def predict_price():
    json = request.get_json()
    data = ps.predict(json["state"],json["district"],json["product"])
    data=eval(data)
    return jsonify(data)

@app.route('/api/user', methods=['POST'])
def add_user():
    json = request.get_json()
    if json["type"]=="farmer":
        table="FARMER"
        columns=["FARMID","FARMNAME","FARMPASS","FARMLOC"]
    elif json["type"]=="consumer":
        table="CONSUMER"
        columns=["CONSID","CONSNAME","CONSPASS","CONSLOC"]
    
    inp={"table":table,"column":columns[0]}
    send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
    userid=send.content
    userid=eval(userid)

    inp={"table":table,"type":"insert","columns":columns,"data":[str(userid),json["name"],json["pass"],json["loc"]]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response(str(userid),status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/product', methods=['POST'])
def add_product():
    json = request.get_json()
    inp={"table":"PRODUCT","column":"PRODID"}
    send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
    prodid=send.content
    prodid=eval(prodid)
    inp={"table":"PRODUCT","type":"insert","columns":["PRODID","PRODTITLE","PRODDESC","PRODTYPE","UPLOADTIME","OWNERID","PRICE","MAXQUANT","MINBUYQUANT"],"data":[str(prodid),json["title"],json["desc"],json["type"],R.current_time(),json["ownerid"],json["price"],json["maxquant"],json["minbuyquant"]]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    price = int(json["price"])/int(json["maxquant"])
    disc = ps.get_discount(json["title"],int(price))
    disc=eval(disc)
    print(disc)
    if disc:
        disc=disc[0]
        print(disc)
        inp={"table":"DEALS","column":"DEALID"}
        send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
        dealid=send.content
        dealid=eval(dealid)
        inp={"table":"DEALS","type":"insert","columns":["DEALID","PRODID","NEWPRICE","DISCOUNT_PERCENT"],"data":[str(dealid),str(prodid),str(price),str(disc)]}
        send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response(str(prodid),status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")
"""
{
	"table":"product",
	"type":"insert",
	"columns":["PRODID","PRODTITLE","PRODDESC","PRODTYPE","UPLOADTIME","OWNERID","PRICE","MAXQUANT","MINBUYQUANT"],
	"data":["1234","Organic Wheat","High Quality Organic Wheat","Wheat","25-01-2020:10-18-16","1234","50000","1000","10"]
}
"""

@app.route('/api/review', methods=['POST'])
def add_review():
    inp={"table":"REVIEW","column":"REVIEWID"}
    send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
    reviewid=send.content
    reviewid=eval(reviewid)
    json = request.get_json()
    inp={"table":"REVIEW","type":"insert","columns":["REVIEWID","REVIEWERID","PRODID","REVIEWDESC","REVIEWSTAR","REVIEWTIME","VERIFIED"],"data":[str(reviewid),json["reviewerid"],json["prodid"],json["reviewdesc"],json["reviewstar"],R.current_time(),json["verified"]]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response(str(reviewid),status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/cart', methods=['POST'])
def add_cart():
    json = request.get_json()

    inp={"table":"PRODUCT","where":"PRODID = "+json["prodid"]+" AND "+json["quantity"]+" >= MINBUYQUANT"}
    send=requests.get('http://127.0.0.1:5000/api/check',json=inp)
    if(send.status_code != requests.codes.ok):
        return Response("Not buying minimum quantity",status=400,mimetype="application/text")
    
    inp={"table":"CART","where":"PRODID = "+json["prodid"]+" AND CONSID = "+json["consid"]}
    send=requests.get('http://127.0.0.1:5000/api/check',json=inp)
    if(send.status_code == requests.codes.ok):
        return Response("Already in CART",status=400,mimetype="application/text")

    inp={"table":"CART","type":"insert","columns":["CONSID","PRODID","QUANTITY"],"data":[json["consid"],json["prodid"],json["quantity"]]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response("1",status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    json = request.get_json()

    inp={"table":"PRODUCT","where":"PRODID = "+json["prodid"]+" AND "+json["quantity"]+" >= MINBUYQUANT"}
    send=requests.get('http://127.0.0.1:5000/api/check',json=inp)
    if(send.status_code != requests.codes.ok):
        return Response("Not buying minimum quantity",status=400,mimetype="application/text")

    inp={"table":"CART","where": "CONSID="+json["consid"]+" AND PRODID = "+json["prodid"]}
    send=requests.get('http://127.0.0.1:5000/api/check',json=inp)
    if(send.status_code != requests.codes.ok):
        return Response("Product not present in cart",status=400,mimetype="application/text")

    inp={"table": "CART","type": "update","columns": ["QUANTITY"],"data": [json["quantity"]],"where": "CONSID = "+json["consid"]+" AND PRODID = "+json["prodid"]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response("1",status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/cart', methods=['DELETE'])
def delete_cart():
    json = request.get_json()
    inp={"table": "CART","type": "delete","where": "CONSID = "+json["consid"]+" AND PRODID = "+json["prodid"]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response("1",status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/product/<prodid>', methods=['DELETE'])
def delete_product(prodid):
    inp={"table": "PRODUCT","type": "delete","where": "PRODID = "+str(prodid)}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response("1",status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/buy', methods=['POST'])
def add_sale():
    inp={"table":"CART","columns":["*"],"where":""}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    inp={"table":"SALES","column":"SALEID"}
    send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
    saleid=send.content
    saleid=eval(saleid)
    for i in range(0,len(data)):
        inp={"table":"SALES","type":"insert","columns":["SALEID","CONSID","PRODID","QUANTITY","BUYTIME"],"data":[str(saleid),str(data[i][0]),str(data[i][1]),str(data[i][2]),R.current_time()]}
        send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)
        if(send.status_code != requests.codes.ok):
            return Response("0",status=500,mimetype="application/text")

    inp={"table":"CART","type":"delete","where":""}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        return Response(str(saleid),status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/image/<imageid>', methods=['GET'])
def get_image(imageid):

    inp={"table":"IMAGE","columns":["IMAGEPATH","IMAGENAME"],"where":"IMAGEID = "+imageid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)

    if(len(data) > 0):
        return Response(data[0][0]+"/"+data[0][1],status=200,mimetype="application/text")
    else:
        return Response("0",status=204,mimetype="application/text")

@app.route('/api/image/<prodid>', methods=['POST'])
def upload(prodid):

    #Accepts all files
    #If user uploads the same file again then a new file will not be created
    inp={"table":"IMAGE","column":"IMAGEID"}
    send=requests.get('http://127.0.0.1:5000/api/GenId',json=inp)
    imageid=send.content
    imageid=eval(imageid)
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1]
    uploads_dir = os.path.join(os.getcwd(), 'Photos\\'+prodid)
    
    path=uploads_dir.replace("\\","/")
    ext=file_ext[1:]
    inp={"table":"IMAGE","type":"insert","columns":["IMAGEID","PRODID","IMAGENAME","IMAGEPATH","IMAGEX"],"data":[str(imageid),prodid,filename,path,ext]}
    send=requests.post('http://127.0.0.1:5000/api/db/write',json=inp)

    if(send.status_code == requests.codes.ok):
        os.makedirs(uploads_dir, exist_ok=True)
        file.save(os.path.join(uploads_dir, filename))
        return Response(str(imageid),status=200,mimetype="application/text")
    else:
        return Response("0",status=500,mimetype="application/text")

@app.route('/api/sub/<term>',methods=["GET"])
def search(term):

    #inp={"table":"product","columns":["PRODTITLE"],"where":""}
    inp={"table":"PRODUCT","columns":["PRODTITLE"],"where":"PRODTITLE LIKE '"+term+"%'"}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    result=[i[0] for i in data]
    """
    result=[]
    for i in data:
        if(i[0].startswith(term)):
            result.append(i[0])
    """
    return jsonify(result)

@app.route('/api/search/<term>',methods=["GET"])
def complete_search(term):

    #inp={"table":"product","columns":["PRODTITLE"],"where":""}
    inp={"table":"PRODUCT","columns":["PRODID"],"where":"PRODTITLE LIKE '"+term+"%'"}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    data=[i[0] for i in data]
    result=[]
    for i in data:
        send=requests.get('http://127.0.0.1:5000/api/product/'+str(i))
        res=send.content
        res=eval(res)
        result.append(res[0])
    return jsonify(result)

@app.route('/api/cart/<consid>', methods=['GET'])
def get_cart(consid):

    #inp={"table":"product","columns":["PRODTITLE"],"where":""}
    inp={"table":"CART","columns":["PRODID","QUANTITY"],"where":"CONSID ="+consid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    result=[]
    for i in data:
        send=requests.get('http://127.0.0.1:5000/api/product/'+str(i[0]))
        res=send.content
        res=eval(res)
        res["BUY_Quanity"] = i[1]
        res["TOTAL_PRICE"] = res["PRICE"] * res["BUY_Quanity"] / res["MAXQUANT"]
        del res["MAXQUANT"]
        del res["MINBUYQUANT"]
        del res["PRICE"]
        result.append(res)
    return jsonify(result)

@app.route('/api/product/<prodid>',methods=["GET"])
def disp_product(prodid):

    inp={"table":"PRODUCT","columns":["PRODTITLE","PRODDESC","PRODTYPE","UPLOADTIME","OWNERID","PRICE","MAXQUANT","MINBUYQUANT"],"where":"PRODID="+prodid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)
    data = data[0]

    #for l in range(0,len(data)):
    inp={"table":"FARMER","columns":["FARMNAME","FARMLOC"],"where":"FARMID="+str(data[4])}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    user=send.content
    user=eval(user)
    for i in user[0]:
        data.append(i)

    inp={"table":"IMAGE","columns":["IMAGEID","IMAGEPATH","IMAGENAME"],"where":"PRODID="+prodid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    img=send.content
    img=eval(img)
    l = []
    for i in img:
        temp = {}
        temp["IMAGEID"] = i[0]
        temp["IMAGEPATH"] = i[1] + "/" + i[2]
        l.append(temp)
    data.append(l)

    #for i in range(0,len(data)):

    temp = {}
    temp["PRODTITLE"] = data[0]
    temp["PRODDESC"] = data[1]
    temp["PRODTYPE"] = data[2]
    temp["UPLOADTIME"] = data[3]
    temp["OWNERID"] = data[4]
    temp["PRICE"] = data[5]
    temp["MAXQUANT"] = data[6]
    temp["MINBUYQUANT"] = data[7]
    temp["FARMNAME"] = data[8]
    temp["FARMLOC"] = data[9]
    temp["IMAGES"] = data[10]
    data = temp

    return jsonify(data)

@app.route('/api/review/<prodid>',methods=["GET"])
def disp_review(prodid):

    inp={"table":"REVIEW","columns":["REVIEWID","REVIEWERID","REVIEWDESC","REVIEWSTAR","REVIEWTIME","VERIFIED"],"where":"PRODID="+prodid}
    send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
    data=send.content
    data=eval(data)

    for l in range(0,len(data)):
        inp={"table":"CONSUMER","columns":["CONSNAME","CONSLOC"],"where":"CONSID="+str(data[l][1])}
        send=requests.get('http://127.0.0.1:5000/api/db/read',json=inp)
        user=send.content
        user=eval(user)
        for i in user[0]:
            data[l].append(i)

    for i in range(0,len(data)):
        temp = {}
        temp["REVIEWID"] = data[i][0]
        temp["REVIEWERID"] = data[i][1]
        temp["REVIEWDESC"] = data[i][2]
        temp["REVIEWSTAR"] = data[i][3]
        temp["REVIEWTIME"] = data[i][4]
        temp["VERIFIED"] = data[i][5]
        temp["CONSNAME"] = data[i][6]
        temp["CONSLOC"] = data[i][7]
        data[i] = temp

    return jsonify(data)

if __name__ == '__main__':
    app.debug=True
    app.run()