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
            # Si se seleccionó una tabla, mostrar los datos
            tabla_seleccionada = request.form.get('tabla')
            if tabla_seleccionada:
                cursor.execute(f"SELECT * FROM {tabla_seleccionada}")
                columnas = [desc[0] for desc in cursor.description]  # Obtener nombres de columnas
                datos = cursor.fetchall()  # Obtener los datos de la tabla seleccionada

        cursor.close()
        connection.close()
        return render_template('master.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)
    else:
        flash("Error: No se pudo conectar a la base de datos master.", "error")
        return redirect(url_for('login'))

# Ruta para agregar una fila (Master)
@app.route('/master/agregar_fila/<tabla>', methods=['GET', 'POST'])
def agregar_fila_master(tabla):
    if request.method == 'POST':
        connection = conectar_master()
        if connection:
            cursor = connection.cursor()
            try:
                # Lógica para insertar en la tabla seleccionada
                if tabla == 'Paciente':
                    cursor.execute(
                        "INSERT INTO Paciente (ID_Paciente, Nombre, Fecha_Nacimiento, Sexo, Dirección, Teléfono, Correo_Electrónico) "
                        "VALUES (:1, :2, :3, :4, :5, :6, :7)",
                        (
                            request.form['id_paciente'],
                            request.form['nombre'],
                            request.form['fecha_nacimiento'],
                            request.form['sexo'],
                            request.form['direccion'],
                            request.form['telefono'],
                            request.form['correo']
                        )
                    )
                elif tabla == 'Medico':
                    cursor.execute(
                        "INSERT INTO Medico (ID_Medico, Nombre, Especialidad, Teléfono, Correo_Electrónico) "
                        "VALUES (:1, :2, :3, :4, :5)",
                        (
                            request.form['id_medico'],
                            request.form['nombre'],
                            request.form['especialidad'],
                            request.form['telefono'],
                            request.form['correo']
                        )
                    )
                # Agregar más casos para otras tablas...
                connection.commit()
                flash("Fila agregada correctamente.", "success")
            except cx_Oracle.DatabaseError as e:
                flash(f"Error al agregar fila: {e}", "error")
            finally:
                cursor.close()
                connection.close()
        return redirect(url_for('master'))
    return render_template('agregar_fila.html', tabla=tabla)

# Ruta para actualizar una fila (Master)
@app.route('/master/actualizar_fila/<tabla>/<int:id>', methods=['GET', 'POST'])
def actualizar_fila_master(tabla, id):
    if request.method == 'POST':
        connection = conectar_master()
        if connection:
            cursor = connection.cursor()
            try:
                # Lógica para actualizar en la tabla seleccionada
                if tabla == 'Paciente':
                    cursor.execute(
                        "UPDATE Paciente SET Nombre = :1, Fecha_Nacimiento = :2, Sexo = :3, Dirección = :4, Teléfono = :5, Correo_Electrónico = :6 "
                        "WHERE ID_Paciente = :7",
                        (
                            request.form['nombre'],
                            request.form['fecha_nacimiento'],
                            request.form['sexo'],
                            request.form['direccion'],
                            request.form['telefono'],
                            request.form['correo'],
                            id
                        )
                    )
                elif tabla == 'Medico':
                    cursor.execute(
                        "UPDATE Medico SET Nombre = :1, Especialidad = :2, Teléfono = :3, Correo_Electrónico = :4 "
                        "WHERE ID_Medico = :5",
                        (
                            request.form['nombre'],
                            request.form['especialidad'],
                            request.form['telefono'],
                            request.form['correo'],
                            id
                        )
                    )
                # Agregar más casos para otras tablas...
                connection.commit()
                flash("Fila actualizada correctamente.", "success")
            except cx_Oracle.DatabaseError as e:
                flash(f"Error al actualizar fila: {e}", "error")
            finally:
                cursor.close()
                connection.close()
        return redirect(url_for('master'))
    else:
        connection = conectar_master()
        if connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {tabla} WHERE ID_{tabla} = :1", (id,))
            fila = cursor.fetchone()
            cursor.close()
            connection.close()
            return render_template('actualizar_fila.html', tabla=tabla, fila=fila)
        else:
            flash("Error: No se pudo conectar a la base de datos.", "error")
            return redirect(url_for('master'))

# Ruta para eliminar una fila (Master)
@app.route('/master/eliminar_fila/<tabla>/<int:id>')
def eliminar_fila_master(tabla, id):
    connection = conectar_master()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"DELETE FROM {tabla} WHERE ID_{tabla} = :1", (id,))
            connection.commit()
            flash("Fila eliminada correctamente.", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Error al eliminar fila: {e}", "error")
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('master'))

# Ruta para borrar auditoría (Master)
@app.route('/master/borrar_auditoria')
def borrar_auditoria_master():
    connection = conectar_master()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM Auditoria")
            connection.commit()
            flash("Auditoría borrada correctamente.", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Error al borrar auditoría: {e}", "error")
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('master'))

# Ruta para el modo Remote
@app.route('/remote')
def remote():
    connection = conectar_remote()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT table_name FROM user_tables WHERE table_name NOT LIKE 'AUDITORIA_%'")
        tablas = [row[0] for row in cursor.fetchall()]

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
        return render_template('remote.html', tablas=tablas, datos=datos, columnas=columnas, tabla_seleccionada=tabla_seleccionada)
    else:
        flash("Error: No se pudo conectar a la base de datos remota.", "error")
        return redirect(url_for('login'))

# Ruta para agregar una fila (Remote)
@app.route('/remote/agregar_fila/<tabla>', methods=['GET', 'POST'])
def agregar_fila_remote(tabla):
    if request.method == 'POST':
        connection = conectar_remote()
        if connection:
            cursor = connection.cursor()
            try:
                # Lógica para insertar en la tabla seleccionada (solo tablas fragmentadas)
                if tabla in ['Paciente', 'Cita', 'Historia_Medica']:
                    if tabla == 'Paciente':
                        cursor.execute(
                            "INSERT INTO Paciente (ID_Paciente, Nombre, Fecha_Nacimiento, Sexo, Dirección, Teléfono, Correo_Electrónico) "
                            "VALUES (:1, :2, :3, :4, :5, :6, :7)",
                            (
                                request.form['id_paciente'],
                                request.form['nombre'],
                                request.form['fecha_nacimiento'],
                                request.form['sexo'],
                                request.form['direccion'],
                                request.form['telefono'],
                                request.form['correo']
                            )
                        )
                    elif tabla == 'Cita':
                        cursor.execute(
                            "INSERT INTO Cita (ID_Cita, Fecha, Hora, ID_Paciente, ID_Medico, Motivo) "
                            "VALUES (:1, :2, :3, :4, :5, :6)",
                            (
                                request.form['id_cita'],
                                request.form['fecha'],
                                request.form['hora'],
                                request.form['id_paciente'],
                                request.form['id_medico'],
                                request.form['motivo']
                            )
                        )
                    elif tabla == 'Historia_Medica':
                        cursor.execute(
                            "INSERT INTO Historia_Medica (ID_Historia, ID_Paciente, Fecha_Registro, Diagnóstico, Tratamiento, Observaciones) "
                            "VALUES (:1, :2, :3, :4, :5, :6)",
                            (
                                request.form['id_historia'],
                                request.form['id_paciente'],
                                request.form['fecha_registro'],
                                request.form['diagnostico'],
                                request.form['tratamiento'],
                                request.form['observaciones']
                            )
                        )
                    connection.commit()
                    flash("Fila agregada correctamente.", "success")
                else:
                    flash("No tienes permisos para agregar filas en esta tabla.", "error")
            except cx_Oracle.DatabaseError as e:
                flash(f"Error al agregar fila: {e}", "error")
            finally:
                cursor.close()
                connection.close()
        return redirect(url_for('remote'))
    return render_template('agregar_fila.html', tabla=tabla)

# Ruta para actualizar una fila (Remote)
@app.route('/remote/actualizar_fila/<tabla>/<int:id>', methods=['GET', 'POST'])
def actualizar_fila_remote(tabla, id):
    if request.method == 'POST':
        connection = conectar_remote()
        if connection:
            cursor = connection.cursor()
            try:
                # Lógica para actualizar en la tabla seleccionada (solo tablas fragmentadas)
                if tabla in ['Paciente', 'Cita', 'Historia_Medica']:
                    if tabla == 'Paciente':
                        cursor.execute(
                            "UPDATE Paciente SET Nombre = :1, Fecha_Nacimiento = :2, Sexo = :3, Dirección = :4, Teléfono = :5, Correo_Electrónico = :6 "
                            "WHERE ID_Paciente = :7",
                            (
                                request.form['nombre'],
                                request.form['fecha_nacimiento'],
                                request.form['sexo'],
                                request.form['direccion'],
                                request.form['telefono'],
                                request.form['correo'],
                                id
                            )
                        )
                    elif tabla == 'Cita':
                        cursor.execute(
                            "UPDATE Cita SET Fecha = :1, Hora = :2, ID_Paciente = :3, ID_Medico = :4, Motivo = :5 "
                            "WHERE ID_Cita = :6",
                            (
                                request.form['fecha'],
                                request.form['hora'],
                                request.form['id_paciente'],
                                request.form['id_medico'],
                                request.form['motivo'],
                                id
                            )
                        )
                    elif tabla == 'Historia_Medica':
                        cursor.execute(
                            "UPDATE Historia_Medica SET Fecha_Registro = :1, Diagnóstico = :2, Tratamiento = :3, Observaciones = :4 "
                            "WHERE ID_Historia = :5",
                            (
                                request.form['fecha_registro'],
                                request.form['diagnostico'],
                                request.form['tratamiento'],
                                request.form['observaciones'],
                                id
                            )
                        )
                    connection.commit()
                    flash("Fila actualizada correctamente.", "success")
                else:
                    flash("No tienes permisos para actualizar filas en esta tabla.", "error")
            except cx_Oracle.DatabaseError as e:
                flash(f"Error al actualizar fila: {e}", "error")
            finally:
                cursor.close()
                connection.close()
        return redirect(url_for('remote'))
    else:
        connection = conectar_remote()
        if connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {tabla} WHERE ID_{tabla} = :1", (id,))
            fila = cursor.fetchone()
            cursor.close()
            connection.close()
            return render_template('actualizar_fila.html', tabla=tabla, fila=fila)
        else:
            flash("Error: No se pudo conectar a la base de datos.", "error")
            return redirect(url_for('remote'))

# Ruta para borrar auditoría (Remote)
@app.route('/remote/borrar_auditoria')
def borrar_auditoria_remote():
    connection = conectar_remote()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM Auditoria")
            connection.commit()
            flash("Auditoría borrada correctamente.", "success")
        except cx_Oracle.DatabaseError as e:
            flash(f"Error al borrar auditoría: {e}", "error")
        finally:
            cursor.close()
            connection.close()
    return redirect(url_for('remote'))

if __name__ == '__main__':
    app.run(debug=True)

