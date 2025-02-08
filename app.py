from flask import Flask, render_template, redirect, url_for, flash, request
import cx_Oracle


app = Flask(__name__)
app.secret_key = 'clave123'  # Necesario para usar mensajes flash

# Configuración de la conexión a Oracle (servidor master)
def conectar_master():
    try:
        dsn = cx_Oracle.makedsn("26.8.164.223", "1521", service_name="orcl")
        connection = cx_Oracle.connect(user="leonardo", password="MasterPass2025", dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Error de conexión (master): {e}")
        return None

# Configuración de la conexión a Oracle (servidor remote)
def conectar_remote():
    try:
        dsn = cx_Oracle.makedsn("26.241.212.154", "1521", service_name="orcl")
        connection = cx_Oracle.connect(user="kevin", password="kevin123", dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Error de conexión (remote): {e}")
        return None

# Ruta principal (página de inicio de sesión)
@app.route('/')
def login():
    return render_template('login.html')

# Ruta para el modo Master
################ SOLO ESTO SE MUEVE PARA LO QUE TIENE QUE VER CON CONSULTAS
@app.route('/master', methods=['GET', 'POST'])
def master():
    connection = conectar_master()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables WHERE table_name NOT LIKE 'AUDITORIA_%'")
        tablas = [row[0] for row in cursor.fetchall()]
        ###METODO 

        datos = None
        columnas = None
        tabla_seleccionada = None

        if request.method == 'POST':
            # Si se seleccionó una tabla, mostrar los datos
            tabla_seleccionada = request.form.get('tabla')
            if tabla_seleccionada:
                cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                columnas = [desc[0] for desc in cursor.description]  # Obtener nombres de columnas
                datos = cursor.fetchall()  # Obtener los datos de la tabla seleccionada
                cursor.close()
                connection.close()
                return render_template('master.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)


        cursor.close()
        connection.close()
        return render_template('master.html', tablas=tablas)
    else:
        flash("Error: No se pudo conectar a la base de datos master.", "error")
        return redirect(url_for('login'))

# Ruta para el modo Remote
@app.route('/remote')
def remote():
    connection = conectar_remote()
    if connection:
        connection.close()  # Cerrar la conexión después de verificar
        return render_template('remote.html')
    else:
        flash("Error: No se pudo conectar a la base de datos remota.", "error")
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
