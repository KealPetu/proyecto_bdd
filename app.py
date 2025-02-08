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
    
@app.route('/master/agregar_fila', methods=['GET', 'POST'])
def agregar_fila_master():
    if request.method == 'POST':
        tabla = request.form['tabla']
        if tabla == 'Medico':
            # Lógica para insertar en la tabla Medico
            id_medico = request.form['id_medico']
            nombre = request.form['nombre']
            especialidad = request.form['especialidad']
            telefono = request.form['telefono']
            correo = request.form['correo']

            connection = conectar_master()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO Medico (ID_Medico, Nombre, Especialidad, Teléfono, Correo_Electrónico) "
                "VALUES (:1, :2, :3, :4, :5)",
                (id_medico, nombre, especialidad, telefono, correo)
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash("Fila agregada correctamente en la tabla Medico.", "success")
        return redirect(url_for('master'))
    return render_template('agregar_fila.html', tipo='master')

@app.route('/remote/agregar_fila', methods=['GET', 'POST'])
def agregar_fila_remote():
    if request.method == 'POST':
        tabla = request.form['tabla']
        if tabla == 'Paciente':
            # Lógica para insertar en la tabla Paciente
            id_paciente = request.form['id_paciente']
            nombre = request.form['nombre']
            fecha_nacimiento = request.form['fecha_nacimiento']
            sexo = request.form['sexo']
            direccion = request.form['direccion']
            telefono = request.form['telefono']
            correo = request.form['correo']

            connection = conectar_remote()
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO Paciente (ID_Paciente, Nombre, Fecha_Nacimiento, Sexo, Dirección, Teléfono, Correo_Electrónico) "
                "VALUES (:1, :2, :3, :4, :5, :6, :7)",
                (id_paciente, nombre, fecha_nacimiento, sexo, direccion, telefono, correo)
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash("Fila agregada correctamente en la tabla Paciente.", "success")
        return redirect(url_for('remote'))
    return render_template('agregar_fila.html', tipo='remote')

@app.route('/master/actualizar_fila/<tabla>/<int:id>', methods=['GET', 'POST'])
def actualizar_fila_master(tabla, id):
    if request.method == 'POST':
        if tabla == 'Medico':
            nombre = request.form['nombre']
            especialidad = request.form['especialidad']
            telefono = request.form['telefono']
            correo = request.form['correo']

            connection = conectar_master()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE Medico SET Nombre = :1, Especialidad = :2, Teléfono = :3, Correo_Electrónico = :4 "
                "WHERE ID_Medico = :5",
                (nombre, especialidad, telefono, correo, id)
            )
            connection.commit()
            cursor.close()
            connection.close()

            flash("Fila actualizada correctamente en la tabla Medico.", "success")
        return redirect(url_for('master'))
    else:
        connection = conectar_master()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {tabla} WHERE ID_{tabla} = :1", (id,))
        fila = cursor.fetchone()
        cursor.close()
        connection.close()
        return render_template('actualizar_fila.html', tipo='master', tabla=tabla, fila=fila)
    
@app.route('/borrar_auditoria', methods=['POST'])
def borrar_auditoria():
    if 'username' in session:
        connection = conectar_master() if session['role'] == 'master' else conectar_remote()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Auditoria")
        connection.commit()
        cursor.close()
        connection.close()

        flash("Auditoría borrada correctamente.", "success")
    return redirect(url_for('master' if session['role'] == 'master' else 'remote'))

if __name__ == '__main__':
    app.run(debug=True)
