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
            if tabla_seleccionada:
                cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                columnas = [desc[0] for desc in cursor.description]  
                datos = cursor.fetchall()

        cursor.close()
        connection.close()
        return render_template('master.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)
    
    else:
        flash("Error: No se pudo conectar a la base de datos master.", "error")
        return redirect(url_for('login'))

# Ruta para crear un nuevo registro
@app.route('/crear/<tabla>', methods=['GET', 'POST'])
def crear(tabla):
    connection = conectar_master()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('master'))

    cursor = connection.cursor()
    cursor.execute(f"SELECT column_name FROM user_tab_columns WHERE table_name = '{tabla}'")
    columnas = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        valores = [request.form[col] for col in columnas]
        placeholders = ", ".join([f":{i+1}" for i in range(len(columnas))])
        query = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        connection.commit()
        flash("Registro agregado correctamente.", "success")
        return redirect(url_for('master'))

    cursor.close()
    connection.close()
    return render_template('crear.html', tabla=tabla, columnas=columnas)

# Ruta para eliminar un registro
@app.route('/eliminar/<tabla>/<id>', methods=['POST'])
def eliminar(tabla, id):
    connection = conectar_master()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('master'))

    cursor = connection.cursor()
    id_col = obtener_columna_id(tabla, cursor)  
    cursor.execute(f"DELETE FROM {tabla} WHERE {id_col} = :1", (id,))
    connection.commit()
    flash("Registro eliminado correctamente.", "success")

    cursor.close()
    connection.close()
    return redirect(url_for('master'))

# Ruta para editar un registro
@app.route('/editar/<tabla>/<id>', methods=['GET', 'POST'])
def editar(tabla, id):
    connection = conectar_master()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('master'))

    cursor = connection.cursor()
    id_col = obtener_columna_id(tabla, cursor)  
    cursor.execute(f"SELECT * FROM {tabla} WHERE {id_col} = :1", (id,))
    registro = cursor.fetchone()
    cursor.execute(f"SELECT column_name FROM user_tab_columns WHERE table_name = '{tabla}'")
    columnas = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        valores = [request.form[col] for col in columnas]
        set_values = ", ".join([f"{col} = :{i+1}" for i, col in enumerate(columnas)])
        query = f"UPDATE {tabla} SET {set_values} WHERE {id_col} = :{len(columnas) + 1}"
        cursor.execute(query, valores + [id])
        connection.commit()
        flash("Registro actualizado correctamente.", "success")
        return redirect(url_for('master'))

    cursor.close()
    connection.close()
    return render_template('editar.html', tabla=tabla, columnas=columnas, registro=registro)

# Obtener el nombre de la columna ID
def obtener_columna_id(tabla, cursor):
    cursor.execute(f"SELECT column_name FROM user_tab_columns WHERE table_name = '{tabla}'")
    return cursor.fetchone()[0]

# Ruta para el modo Remote
@app.route('/remote', methods=['GET', 'POST'])
def remote():
    connection = conectar_remote()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables WHERE table_name LIKE '%_Replica'")
        tablas_replicadas = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT table_name FROM user_tables WHERE table_name NOT LIKE '%_Replica' AND table_name NOT LIKE 'AUDITORIA_%'")
        tablas_fragmentadas = [row[0] for row in cursor.fetchall()]

        datos = None
        columnas = None
        tabla_seleccionada = None

        if request.method == 'POST':
            tabla_seleccionada = request.form.get('tabla')
            if tabla_seleccionada:
                cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                columnas = [desc[0] for desc in cursor.description]  
                datos = cursor.fetchall()

        cursor.close()
        connection.close()
        return render_template('remote.html', tablas_replicadas=tablas_replicadas, tablas_fragmentadas=tablas_fragmentadas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)
    
    else:
        flash("Error: No se pudo conectar a la base de datos remota.", "error")
        return redirect(url_for('login'))

# Ruta para crear un nuevo registro en Remote (solo tablas fragmentadas)
@app.route('/remote/crear/<tabla>', methods=['GET', 'POST'])
def remote_crear(tabla):
    connection = conectar_remote()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('remote'))

    cursor = connection.cursor()
    cursor.execute(f"SELECT column_name FROM user_tab_columns WHERE table_name = '{tabla}'")
    columnas = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        valores = [request.form[col] for col in columnas]
        placeholders = ", ".join([f":{i+1}" for i in range(len(columnas))])
        query = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({placeholders})"
        cursor.execute(query, valores)
        connection.commit()
        flash("Registro agregado correctamente.", "success")
        return redirect(url_for('remote'))

    cursor.close()
    connection.close()
    return render_template('crear.html', tabla=tabla, columnas=columnas)

# Ruta para editar un registro en Remote (solo tablas fragmentadas)
@app.route('/remote/editar/<tabla>/<id>', methods=['GET', 'POST'])
def remote_editar(tabla, id):
    connection = conectar_remote()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('remote'))

    cursor = connection.cursor()
    id_col = obtener_columna_id(tabla, cursor)  
    cursor.execute(f"SELECT * FROM {tabla} WHERE {id_col} = :1", (id,))
    registro = cursor.fetchone()
    cursor.execute(f"SELECT column_name FROM user_tab_columns WHERE table_name = '{tabla}'")
    columnas = [row[0] for row in cursor.fetchall()]

    if request.method == 'POST':
        valores = [request.form[col] for col in columnas]
        set_values = ", ".join([f"{col} = :{i+1}" for i, col in enumerate(columnas)])
        query = f"UPDATE {tabla} SET {set_values} WHERE {id_col} = :{len(columnas) + 1}"
        cursor.execute(query, valores + [id])
        connection.commit()
        flash("Registro actualizado correctamente.", "success")
        return redirect(url_for('remote'))

    cursor.close()
    connection.close()
    return render_template('editar.html', tabla=tabla, columnas=columnas, registro=registro)

# Ruta para eliminar un registro en Remote (solo tablas de auditoría)
@app.route('/remote/eliminar/<tabla>/<id>', methods=['POST'])
def remote_eliminar(tabla, id):
    connection = conectar_remote()
    if not connection:
        flash("Error al conectar con la base de datos.", "error")
        return redirect(url_for('remote'))

    cursor = connection.cursor()
    id_col = obtener_columna_id(tabla, cursor)  
    cursor.execute(f"DELETE FROM {tabla} WHERE {id_col} = :1", (id,))
    connection.commit()
    flash("Registro eliminado correctamente.", "success")

    cursor.close()
    connection.close()
    return redirect(url_for('remote'))

if __name__ == '__main__':
    app.run(debug=True)
