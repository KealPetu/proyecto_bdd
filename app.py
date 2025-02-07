from flask import Flask, render_template, request, redirect, url_for, session
import cx_Oracle

app = Flask(__name__)

# Configuración de la conexión a Oracle
def get_db_connection():
    dsn = cx_Oracle.makedsn("host", "port", service_name="servicio")
    connection = cx_Oracle.connect(user="usuario", password="contraseña", dsn=dsn)
    return connection

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/paciente')
def paciente():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Paciente")
    pacientes = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('paciente.html', pacientes=pacientes)

@app.route('/paciente/insertar', methods=['POST'])
def insertar_paciente():
    id_paciente = request.form['id_paciente']
    nombre = request.form['nombre']
    fecha_nacimiento = request.form['fecha_nacimiento']
    sexo = request.form['sexo']
    direccion = request.form['direccion']
    telefono = request.form['telefono']
    correo = request.form['correo']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO Paciente (ID_Paciente, Nombre, Fecha_Nacimiento, Sexo, Dirección, Teléfono, Correo_Electrónico) "
        "VALUES (:1, :2, :3, :4, :5, :6, :7)",
        (id_paciente, nombre, fecha_nacimiento, sexo, direccion, telefono, correo)
    )
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('paciente'))

@app.route('/paciente/editar/<int:id_paciente>', methods=['GET', 'POST'])
def editar_paciente(id_paciente):
    if request.method == 'POST':
        nombre = request.form['nombre']
        fecha_nacimiento = request.form['fecha_nacimiento']
        sexo = request.form['sexo']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        correo = request.form['correo']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE Paciente SET Nombre = :1, Fecha_Nacimiento = :2, Sexo = :3, Dirección = :4, Teléfono = :5, Correo_Electrónico = :6 "
            "WHERE ID_Paciente = :7",
            (nombre, fecha_nacimiento, sexo, direccion, telefono, correo, id_paciente)
        )
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('paciente'))
    else:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Paciente WHERE ID_Paciente = :1", (id_paciente,))
        paciente = cursor.fetchone()
        cursor.close()
        connection.close()
        return render_template('editar_paciente.html', paciente=paciente)

@app.route('/paciente/eliminar/<int:id_paciente>')
def eliminar_paciente(id_paciente):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Paciente WHERE ID_Paciente = :1", (id_paciente,))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect(url_for('paciente'))

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Necesario para manejar sesiones

# Usuarios de ejemplo (en un caso real, usa una base de datos)
USERS = {
    'master': {'password': 'master123', 'role': 'master'},
    'remote': {'password': 'remote123', 'role': 'remote'}
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Verificar credenciales
        if username in USERS and USERS[username]['password'] == password and USERS[username]['role'] == role:
            session['username'] = username
            session['role'] = role
            if role == 'master':
                return redirect(url_for('master'))
            else:
                return redirect(url_for('remote'))
        else:
            return "Credenciales incorrectas o rol no válido."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/master')
def master():
    if 'username' in session and session['role'] == 'master':
        return render_template('master.html')
    return redirect(url_for('login'))

@app.route('/remote')
def remote():
    if 'username' in session and session['role'] == 'remote':
        return render_template('remote.html')
    return redirect(url_for('login'))

@app.route('/ver_replicas')
def ver_replicas():
    if 'username' in session and session['role'] == 'remote':
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Medico_Replica")
        medicos = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('ver_replicas.html', medicos=medicos)
    return redirect(url_for('login'))