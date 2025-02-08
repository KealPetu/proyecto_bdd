from flask import Flask, render_template, redirect, url_for, flash, request
import cx_Oracle

app = Flask(__name__)
app.secret_key = 'clave123'  # Necessary for flash messages

# Master connection configuration
def conectar_master():
    try:
        dsn = cx_Oracle.makedsn("26.8.164.223", "1521", service_name="orcl")
        connection = cx_Oracle.connect(user="leonardo", password="MasterPass2025", dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Error de conexión (master): {e}")
        return None

# Remote connection configuration
def conectar_remote():
    try:
        dsn = cx_Oracle.makedsn("26.241.212.154", "1521", service_name="orcl")
        connection = cx_Oracle.connect(user="kevin", password="kevin123", dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Error de conexión (remote): {e}")
        return None

# Main login route
@app.route('/')
def login():
    return render_template('login.html')

# Master Route
@app.route('/master', methods=['GET', 'POST'])
def master():
    connection = conectar_master()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables WHERE table_name NOT LIKE 'AUDITORIA_%'")
        tablas = [row[0] for row in cursor.fetchall()]

        datos = None
        columnas = None
        tabla_seleccionada = None

        if request.method == 'POST':
            tabla_seleccionada = request.form.get('tabla')
            accion = request.form.get('accion')

            if tabla_seleccionada:
                if accion == 'leer':
                    cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                    columnas = [desc[0] for desc in cursor.description]
                    datos = cursor.fetchall()
                elif accion == 'insertar':
                    valores = request.form.get('valores')
                    cursor.execute(f"INSERT INTO {tabla_seleccionada} VALUES ({valores})")
                    connection.commit()
                elif accion == 'actualizar':
                    set_values = request.form.get('set_values')
                    condition = request.form.get('condition')
                    cursor.execute(f"UPDATE {tabla_seleccionada} SET {set_values} WHERE {condition}")
                    connection.commit()
                elif accion == 'eliminar':
                    condition = request.form.get('condition')
                    cursor.execute(f"DELETE FROM {tabla_seleccionada} WHERE {condition}")
                    connection.commit()

                cursor.close()
                connection.close()
                return render_template('master.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)

        cursor.close()
        connection.close()
        return render_template('master.html', tablas=tablas)
    else:
        flash("Error: No se pudo conectar a la base de datos master.", "error")
        return redirect(url_for('login'))

# Remote Route
@app.route('/remote', methods=['GET', 'POST'])
def remote():
    connection = conectar_remote()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables WHERE table_name LIKE 'FRAGMENTADA_%' OR table_name LIKE 'REPLICA_%'")
        tablas = [row[0] for row in cursor.fetchall()]

        datos = None
        columnas = None
        tabla_seleccionada = None

        if request.method == 'POST':
            tabla_seleccionada = request.form.get('tabla')
            accion = request.form.get('accion')

            if tabla_seleccionada:
                # Only allow CRUD on Fragmented tables (FRAGMENTADA_)
                if "FRAGMENTADA_" in tabla_seleccionada:
                    if accion in ['leer', 'insertar', 'actualizar']:
                        cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                        columnas = [desc[0] for desc in cursor.description]
                        datos = cursor.fetchall()
                        if accion == 'insertar':
                            valores = request.form.get('valores')
                            cursor.execute(f"INSERT INTO {tabla_seleccionada} VALUES ({valores})")
                            connection.commit()
                        elif accion == 'actualizar':
                            set_values = request.form.get('set_values')
                            condition = request.form.get('condition')
                            cursor.execute(f"UPDATE {tabla_seleccionada} SET {set_values} WHERE {condition}")
                            connection.commit()

                # Allow only read access to Replicated tables (REPLICA_)
                elif "REPLICA_" in tabla_seleccionada and accion == 'leer':
                    cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                    columnas = [desc[0] for desc in cursor.description]
                    datos = cursor.fetchall()

                cursor.close()
                connection.close()
                return render_template('remote.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)

        cursor.close()
        connection.close()
        return render_template('remote.html', tablas=tablas)
    else:
        flash("Error: No se pudo conectar a la base de datos remota.", "error")
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

