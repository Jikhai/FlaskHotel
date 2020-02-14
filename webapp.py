import time
from flask import *
import sys
import psycopg2


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
    session['email'] = request.form['email']
    #print(request.form['email'])
    #print(session['email'])
    #print(session)
    return actionmenu(session)

@app.route('/after_nouveau_compte/', methods=['POST']) #compte crée
def after_nouveau_compte():
    session['name'] = request.form['name']
    session['email'] = request.form['mail']
    session['pass'] = request.form['pass']
    #print( session['name'])
    #print(session['email'])
    #print( session['pass'])
    pgsql_ajout_client(session['name'],session['email'],session['pass'])
    return actionmenu(session)

@app.route('/back_to_menu/', methods=['POST','GET'])
def back_to_menu():
    return actionmenu(session)

@app.route("/menu/")
def actionmenu(session):
    #print(str(session))
    #print("si la ligne précédente est vide ma vie est un échec")
    #print(session['email'])
    dbresponse=pgsql_client_by_mail(session['email'])
    #print(dbresponse)
    session['name']=dbresponse[0][0]
    #print(session['name'])
    return render_template("choisir-action.html", session=session)

@app.route('/consult_reserv/', methods=['POST','GET'])
def consult_reserv():
    return render_template("consult-reserv.html", session=session)

@app.route('/choisir_chambre/', methods=['POST','GET'])
def choisir_chambre():
    return render_template("choisir-chambre.html", session=session)

@app.route('/choisir_conso/', methods=['POST','GET'])
def choisir_conso():
    return render_template("choisir-conso.html", session=session, rows=liste_produits() )

@app.route('/confirmation_conso/', methods=['POST','GET'])
def confirm_conso():
    consoNAME = pgsql_product_by_id(request.form['consoID'])
    consoNAME = consoNAME[0][0]
    consoQTE = request.form['consoID']
    return render_template("confirm-conso.html", session=session, consoQTE=consoQTE, consoNAME=consoNAME)

@app.route('/payer_reserv/', methods=['POST','GET'])
def payer_reserv():
    return render_template("payer-reserv.html", session=session)



@app.route('/after_choisir_nouveau_compte/')
def after_choisir_nouveau_compte(error=None):
    session.clear()
    return render_template("nouveau-compte.html",hasError=error, session=session)

# ---------- BDD SETUP -------------
#interaction avec PostGres
def pgsql_connect():
    #try connection
    ##if session['db'] is None:
    try:
        db = psycopg2.connect("host=dbserver.emi.u-bordeaux.fr dbname=adanguin user=adanguin")
        return db
    except Exception as e :
        flash('connexion error')
        return redirect(url_for('hello',error=str(e)))
    #return session['db']

#------------------------------------ DB Commands -----

def liste_mail():
    return pgsql_select('select mail from Hotel2019.Client;')

def liste_chambres(idclient):
        return pgsql_select('select * from Hotel2019.Chambres;')

def liste_reserv():
        return pgsql_select('select * from Hotel2019.Reservation where idclient=\'%s\';'% (idclient))

def liste_produits():
    return pgsql_select('select * from Hotel2019.Bar;')

def pgsql_ajout_client(newname,newmail,newpassword):
    #print(newname,newmail,newpassword)
    return pgsql_insert('insert into Hotel2019.Client values(DEFAULT,\'%s\',\'%s\',\'%s\');' % (newname, newmail, newpassword))

def pgsql_client_by_mail(mail):
    #print(mail)
    return pgsql_select('select nom from Hotel2019.Client where mail=\'%s\';' % (mail))

def pgsql_product_by_id(ID):
    print(ID)
    return pgsql_select('select nomproduit from Hotel2019.Bar where idproduit=\'%s\';' % (ID))

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
     #flash(command)
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
