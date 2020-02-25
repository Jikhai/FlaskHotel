import time
from flask import *
import sys
import psycopg2
from datetime import *
from datetime import timedelta

today= date.today().strftime("%d/%m/%Y")
date= date.today()
tomorrow= datetime.now()+timedelta(days=1)
#DO NOT TOUCH THIS
app = Flask(__name__)
app.secret_key = 'some_secret'

# flask stuff ----------
@app.route("/")

@app.route("/<error>")
def hello(error=None):
    session.clear()
    return render_template("choisir-mail.html", rows=liste_mail(), hasError=error, session=session)

@app.route('/after_choisir_email/', methods=['POST','GET'])
def after_choisir_email():
    email= request.form['email']
    passw= request.form['passw']
    if passw==checkpassw(pgsql_clientid_by_mail(email)[0][0])[0][0]:
        session['email'] = request.form['email']
        return actionmenu(session)
    else :
        return hello(error="Mauvais mot de passe")

@app.route('/after_choisir_nouveau_compte/')
def after_choisir_nouveau_compte(error=None):
    session.clear()

    return render_template("nouveau-compte.html",hasError=error, session=session)

@app.route('/after_nouveau_compte/', methods=['POST','GET']) #compte crée
def after_nouveau_compte():
    name = request.form['name']
    email = request.form['mail']
    passw = request.form['pass']
    for i in checkmail():
        if i[0] == email:
            #print("oulah")
            return hello(error= "Mail déjà existant dans la base de données")
    else :
        pgsql_ajout_client(name,email,passw)
        session['email'] = request.form['mail']
        return actionmenu(session)

@app.route('/back_to_menu/', methods=['POST','GET'])
def back_to_menu():
    return actionmenu(session)


@app.route("/menu/")
def actionmenu(session):
    session['name']=pgsql_client_by_mail(session['email'])[0][0]
    session['reserv']=pgsql_exist_reserv(pgsql_clientid_by_mail(session['email'])[0][0])[0][0]

    print (session['reserv'])
    if session['reserv']==False :
        return render_template("no-reserv.html", session=session, jour=date.day, mois=date.month, annee=date.year)
    elif session['reserv']==True :
        date_fin = pgsql_reserv_active(pgsql_clientid_by_mail(session['email'])[0][0])[0][0]
        return render_template("choisir-action.html", session=session, jour=date.day, mois=date.month, annee=date.year, date_fin=date_fin)
    else :
        return hello(error=None)

# ------------------- Réservations
@app.route('/consult_reserv/', methods=['POST','GET'])
def consult_reserv():
    rows= pgsql_liste_reserv(pgsql_clientid_by_mail(session['email'])[0][0])
    rows2= pgsql_list_paid(pgsql_reserv_active_id(pgsql_clientid_by_mail(session['email'])[0][0])[0][0])
    return render_template("consult-reserv.html", session=session, rows=rows, rows2=rows2)

@app.route('/choisir_chambre/', methods=['POST','GET'])
def choisir_chambre():

    return render_template("choisir-chambre.html", session=session, rows=liste_chambres(), date=today, tomorrow=tomorrow)

@app.route('/confirmation_reserv/', methods=['POST','GET'])
def confirm_reserv():
    chambreID = request.form['chambreID']
    print(chambreID)
    date_debut = request.form['date_debut']
    print (date_debut)
    date_fin = request.form['date_fin']
    print(date_fin)
    pgsql_ajout_reserv(chambreID,date_debut,date_fin,pgsql_clientid_by_mail(session['email'])[0][0])
    return render_template("confirm-reserv.html", session=session, chambreID=chambreID, date_debut=date_debut, date_fin=date_fin)
# ------------------- Consommations
@app.route('/choisir_conso/', methods=['POST','GET'])
def choisir_conso():
    return render_template("choisir-conso.html", session=session, rows=liste_produits() )

@app.route('/confirmation_conso/', methods=['POST','GET'])
def confirm_conso():
    consoNAME = pgsql_product_by_id(request.form['consoID'])
    consoNAME = consoNAME[0][0]
    consoQTE = request.form['consoQTE']
    pgsql_ajout_consommation(pgsql_clientid_by_mail(session ['email'])[0][0],request.form['consoID'],consoQTE)
    return render_template("confirm-conso.html", session=session, consoQTE=consoQTE, consoNAME=consoNAME)
# ------------------- Autres
@app.route('/payer_reserv/', methods=['POST','GET'])
def payer_reserv():
    d,f,n,t=pgsql_facture(pgsql_clientid_by_mail(session['email'])[0][0])
    tch= int((f-d).days)*t
    tco=pgsql_somme_conso(pgsql_clientid_by_mail(session['email'])[0][0],d,f)
    sum=tch+tco
    paid=pgsql_get_paid(pgsql_reserv_active_id(pgsql_clientid_by_mail(session['email'])[0][0])[0][0])[0][0]
    if paid == None :
        paid=0
    remain = sum - paid
    return render_template("payer-reserv.html", session=session, d=d,f=f,n=n,t=t,tch=tch,tco=tco,sum=sum,paid=paid,remain=remain)

@app.route('/confirm_paiement/', methods=['POST','GET'])
def confirm_paiement():
    d,f,n,t=pgsql_facture(pgsql_clientid_by_mail(session['email'])[0][0])
    tch= int((f-d).days)*t
    tco=pgsql_somme_conso(pgsql_clientid_by_mail(session['email'])[0][0],d,f)
    sum=tch+tco
    paidOld=pgsql_get_paid(pgsql_reserv_active_id(pgsql_clientid_by_mail(session['email'])[0][0])[0][0])[0][0]
    paid=float(request.form['amount'])
    if paidOld==None :
        paidOld=0
    remain = sum - paidOld - paid
    print(pgsql_reserv_active_id(pgsql_clientid_by_mail(session['email'])[0][0])[0][0])
    pgsql_paiement(paid,pgsql_reserv_active_id(pgsql_clientid_by_mail(session['email'])[0][0])[0][0])
    return render_template("confirm-paiement.html", session=session, paid=paid,remain=remain)




# ---------- BDD SETUP -------------
#interaction avec PostGres6


def pgsql_connect():
    try:
        db = psycopg2.connect("host=dbserver.emi.u-bordeaux.fr dbname=adanguin user=adanguin")
        return db
    except Exception as e :
        flash('connexion error')
        return redirect(url_for('hello',error=str(e)))

#------------------------------------ DB Commands -----

def checkmail():
    return pgsql_select('select mail from Hotel2019.Client;')
def checkpassw(idclient):
    return pgsql_select('select pass from Hotel2019.Client where idclient=\'%s\';'% (idclient))

def liste_mail():
    return pgsql_select('select mail from Hotel2019.Client;')

def liste_chambres():
        return pgsql_select('select * from Hotel2019.Chambre where numero NOT IN (select numero from Hotel2019.Reservation where date_fin>=current_date and date_debut<=current_date);')

def liste_chambres_occupees():
        return pgsql_select('select numero from Hotel2019.Reservation where date_fin>=current_date;')


def liste_produits():
    return pgsql_select('select * from Hotel2019.Bar;')

def pgsql_reserv_active(idclient):
    return pgsql_select('select date_fin from hotel2019.Reservation where idclient=\'%s\' and date_fin>=current_date ;'% (idclient))

def pgsql_reserv_active_id(idclient):
    return pgsql_select('select idreserv from hotel2019.Reservation where idclient=\'%s\' and date_debut<=current_date and date_fin>=current_date ;'% (idclient))

def pgsql_exist_reserv(idclient):
    return pgsql_select('select exists (select true from hotel2019.Reservation where idclient=\'%s\' and date_fin>=current_date );'% (idclient))

def pgsql_liste_reserv(idclient):
    return pgsql_select('select * from Hotel2019.Reservation where idclient=\'%s\';'% (idclient))

def pgsql_facture(idclient):
    temp = pgsql_select('select date_debut, date_fin, numero from hotel2019.Reservation where idclient=\'%s\' and date_fin>=current_date ;'% (idclient))
    d=temp[0][0]
    f=temp[0][1]
    n=temp[0][2]
    temp = pgsql_select('select tarif from hotel2019.chambre where numero=\'%s\';' %(n))
    t= temp[0][0]
    return d,f,n,t
def pgsql_tarifproduit(id):
    return pgsql_select('select tarif from hotel2019.bar where idproduit=\'%s\';' %(id))

def pgsql_somme_conso(idclient,d,f):
    sum=0
    temp = pgsql_select('select idproduit,qte from hotel2019.consommation where idclient=\'%s\' and dateconso<=\'%s\' and dateconso>=\'%s\';'%(idclient,f,d))
    for row in temp :
        t=pgsql_tarifproduit(row[0])[0][0]
        sum=sum+(t*row[1])
    return sum

def pgsql_get_paid(id):
        temp = pgsql_select('select sum(somme) from hotel2019.paiement where "Numreservation"=\'%s\';'%(int(id)))
        return temp

def pgsql_list_paid(id):
        temp = pgsql_select('select * from hotel2019.paiement where "Numreservation"=\'%s\';'%(int(id)))
        return temp
def pgsql_client_by_mail(mail):
    return pgsql_select('select nom from Hotel2019.Client where mail=\'%s\';' % (mail))

def pgsql_clientid_by_mail(mail):
    return pgsql_select('select idclient from Hotel2019.Client where mail=\'%s\';' % (mail))

def pgsql_product_by_id(ID):
    return pgsql_select('select nomproduit from Hotel2019.Bar where idproduit=\'%s\';' % (ID))

# -- Commands that WRITE to the DB ---

def pgsql_ajout_client(newname,newmail,newpassword):
    return pgsql_insert('insert into Hotel2019.Client values(DEFAULT,\'%s\',\'%s\',\'%s\');' % (newname, newmail, newpassword))

def pgsql_ajout_consommation(idclient,idproduit,qte):
    return pgsql_insert('insert into Hotel2019.Consommation values(DEFAULT,\'%s\',\'%s\',\'%s\',current_date);' % (idclient,idproduit,qte))

def pgsql_ajout_reserv(chambreID,date_debut,date_fin,clientID):
    print(chambreID)
    return pgsql_insert('insert into Hotel2019.Reservation values(\'%s\',\'%s\',\'%s\',\'%s\',DEFAULT);' % (chambreID,date_debut,date_fin,clientID))

def pgsql_paiement(somme,id):
    return pgsql_insert('insert into Hotel2019.paiement values(\'%s\',current_date,\'%s\');' % ((float(somme),int(id))))
# -------------------------------------- DB ACCESS & CONTROLS ------
def pgsql_select(command):
    db = pgsql_connect()

    cursor = db.cursor()
    try:
        cursor.execute(command)
        rows = cursor.fetchall()

        cursor.close()
        db.close()
        print('passed')
        return rows
    except Exception as e :
        print('failed')
        flash('sorry, this service is unavailable')
        return redirect(url_for('hello',error=str(e)))

def pgsql_insert(command):
     db = pgsql_connect()
     cursor = db.cursor()
     try:
        cursor.execute(command)
        nb = cursor.rowcount
        cursor.close()
        db.commit()
        print('passed')
        return nb
     except Exception as e:
            print(e)
            print('failed')
            flash ('Service Unavailable')
            return redirect(url_for('hello', error=str(e)))
#--------------------------------------------------------------------------------------------
#DO NOT TOUCH THIS
if __name__ == "__main__":
   app.run(debug=True)
