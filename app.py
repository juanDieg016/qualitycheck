from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)


def conectar_db():
    conexion = sqlite3.connect("qualitycheck.db")
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_base_datos():
    conexion = conectar_db()

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            responsable TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS requisitos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            tipo TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)
        )
    """)

    conexion.execute("""
        CREATE TABLE IF NOT EXISTS casos_prueba (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requisito_id INTEGER NOT NULL,
            codigo TEXT NOT NULL,
            objetivo TEXT NOT NULL,
            precondiciones TEXT NOT NULL,
            pasos TEXT NOT NULL,
            datos_entrada TEXT,
            resultado_esperado TEXT NOT NULL,
            resultado_obtenido TEXT,
            estado TEXT NOT NULL,
            fecha_ejecucion TEXT,
            ejecutor TEXT,
            observaciones TEXT,
            FOREIGN KEY (requisito_id) REFERENCES requisitos(id)
        )
    """)
    conexion.execute("""
    CREATE TABLE IF NOT EXISTS defectos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        caso_prueba_id INTEGER,
        codigo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        pasos_reproducir TEXT NOT NULL,
        severidad TEXT NOT NULL,
        responsable TEXT NOT NULL,
        estado TEXT NOT NULL,
        evidencia TEXT,
        FOREIGN KEY (caso_prueba_id) REFERENCES casos_prueba(id)
    )
""")
    conexion.execute("""
    CREATE TABLE IF NOT EXISTS evaluaciones_calidad (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proyecto_id INTEGER NOT NULL,
        caracteristica TEXT NOT NULL,
        criterio TEXT NOT NULL,
        metodo_medicion TEXT NOT NULL,
        resultado TEXT NOT NULL,
        porcentaje REAL,
        evidencia TEXT,
        observaciones TEXT,
        FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)
    )
""")

    conexion.commit()
    conexion.close()


@app.route("/")
def inicio():
    return redirect(url_for("listar_proyectos"))


# =========================
# PROYECTOS
# =========================

@app.route("/proyectos")
def listar_proyectos():
    conexion = conectar_db()

    proyectos = conexion.execute(
        "SELECT * FROM proyectos ORDER BY id DESC"
    ).fetchall()

    conexion.close()

    return render_template(
        "proyectos.html",
        proyectos=proyectos
    )


@app.route("/proyectos/nuevo", methods=["GET", "POST"])
def nuevo_proyecto():

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        responsable = request.form["responsable"]
        estado = request.form["estado"]

        conexion = conectar_db()

        conexion.execute("""
            INSERT INTO proyectos (
                nombre,
                descripcion,
                responsable,
                fecha_creacion,
                estado
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            nombre,
            descripcion,
            responsable,
            date.today().isoformat(),
            estado
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_proyectos"))

    return render_template("nuevo_proyecto.html")


@app.route("/proyectos/editar/<int:id>", methods=["GET", "POST"])
def editar_proyecto(id):
    conexion = conectar_db()

    proyecto = conexion.execute(
        "SELECT * FROM proyectos WHERE id = ?",
        (id,)
    ).fetchone()

    if proyecto is None:
        conexion.close()
        return "Proyecto no encontrado", 404

    if request.method == "POST":
        nombre = request.form["nombre"]
        descripcion = request.form["descripcion"]
        responsable = request.form["responsable"]
        estado = request.form["estado"]

        conexion.execute("""
            UPDATE proyectos
            SET nombre = ?,
                descripcion = ?,
                responsable = ?,
                estado = ?
            WHERE id = ?
        """, (
            nombre,
            descripcion,
            responsable,
            estado,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_proyectos"))

    conexion.close()

    return render_template(
        "editar_proyecto.html",
        proyecto=proyecto
    )


@app.route("/proyectos/eliminar/<int:id>", methods=["POST"])
def eliminar_proyecto(id):
    conexion = conectar_db()

    conexion.execute(
        "DELETE FROM proyectos WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar_proyectos"))


# =========================
# REQUISITOS
# =========================

@app.route("/requisitos")
def listar_requisitos():
    conexion = conectar_db()

    requisitos = conexion.execute("""
        SELECT
            requisitos.id,
            requisitos.codigo,
            requisitos.descripcion,
            requisitos.tipo,
            requisitos.prioridad,
            requisitos.estado,
            proyectos.nombre AS proyecto
        FROM requisitos
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY requisitos.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "requisitos.html",
        requisitos=requisitos
    )


@app.route("/requisitos/nuevo", methods=["GET", "POST"])
def nuevo_requisito():
    conexion = conectar_db()

    proyectos = conexion.execute(
        "SELECT id, nombre FROM proyectos ORDER BY nombre"
    ).fetchall()

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        codigo = request.form["codigo"]
        descripcion = request.form["descripcion"]
        tipo = request.form["tipo"]
        prioridad = request.form["prioridad"]
        estado = request.form["estado"]

        conexion.execute("""
            INSERT INTO requisitos (
                proyecto_id,
                codigo,
                descripcion,
                tipo,
                prioridad,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            proyecto_id,
            codigo,
            descripcion,
            tipo,
            prioridad,
            estado
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_requisitos"))

    conexion.close()

    return render_template(
        "nuevo_requisito.html",
        proyectos=proyectos
    )


@app.route("/requisitos/editar/<int:id>", methods=["GET", "POST"])
def editar_requisito(id):
    conexion = conectar_db()

    requisito = conexion.execute(
        "SELECT * FROM requisitos WHERE id = ?",
        (id,)
    ).fetchone()

    proyectos = conexion.execute(
        "SELECT id, nombre FROM proyectos ORDER BY nombre"
    ).fetchall()

    if requisito is None:
        conexion.close()
        return "Requisito no encontrado", 404

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        codigo = request.form["codigo"]
        descripcion = request.form["descripcion"]
        tipo = request.form["tipo"]
        prioridad = request.form["prioridad"]
        estado = request.form["estado"]

        conexion.execute("""
            UPDATE requisitos
            SET proyecto_id = ?,
                codigo = ?,
                descripcion = ?,
                tipo = ?,
                prioridad = ?,
                estado = ?
            WHERE id = ?
        """, (
            proyecto_id,
            codigo,
            descripcion,
            tipo,
            prioridad,
            estado,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_requisitos"))

    conexion.close()

    return render_template(
        "editar_requisito.html",
        requisito=requisito,
        proyectos=proyectos
    )


@app.route("/requisitos/eliminar/<int:id>", methods=["POST"])
def eliminar_requisito(id):
    conexion = conectar_db()

    conexion.execute(
        "DELETE FROM requisitos WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar_requisitos"))

@app.route("/casos-prueba")
def listar_casos_prueba():
    conexion = conectar_db()

    casos = conexion.execute("""
        SELECT
            casos_prueba.id,
            casos_prueba.codigo,
            casos_prueba.objetivo,
            casos_prueba.estado,
            casos_prueba.fecha_ejecucion,
            casos_prueba.ejecutor,
            requisitos.codigo AS requisito,
            proyectos.nombre AS proyecto
        FROM casos_prueba
        INNER JOIN requisitos
            ON casos_prueba.requisito_id = requisitos.id
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY casos_prueba.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "casos_prueba.html",
        casos=casos
    )

@app.route("/casos-prueba/nuevo", methods=["GET", "POST"])
def nuevo_caso_prueba():
    conexion = conectar_db()

    requisitos = conexion.execute("""
        SELECT
            requisitos.id,
            requisitos.codigo,
            requisitos.descripcion,
            proyectos.nombre AS proyecto
        FROM requisitos
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY proyectos.nombre, requisitos.codigo
    """).fetchall()

    if request.method == "POST":
        requisito_id = request.form["requisito_id"]
        codigo = request.form["codigo"]
        objetivo = request.form["objetivo"]
        precondiciones = request.form["precondiciones"]
        pasos = request.form["pasos"]
        datos_entrada = request.form["datos_entrada"]
        resultado_esperado = request.form["resultado_esperado"]
        resultado_obtenido = request.form["resultado_obtenido"]
        estado = request.form["estado"]
        fecha_ejecucion = request.form["fecha_ejecucion"]
        ejecutor = request.form["ejecutor"]
        observaciones = request.form["observaciones"]

        conexion.execute("""
            INSERT INTO casos_prueba (
                requisito_id,
                codigo,
                objetivo,
                precondiciones,
                pasos,
                datos_entrada,
                resultado_esperado,
                resultado_obtenido,
                estado,
                fecha_ejecucion,
                ejecutor,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            requisito_id,
            codigo,
            objetivo,
            precondiciones,
            pasos,
            datos_entrada,
            resultado_esperado,
            resultado_obtenido,
            estado,
            fecha_ejecucion,
            ejecutor,
            observaciones
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_casos_prueba"))

    conexion.close()

    return render_template(
        "nuevo_caso_prueba.html",
        requisitos=requisitos
    )
@app.route("/casos-prueba/editar/<int:id>", methods=["GET", "POST"])
def editar_caso_prueba(id):
    conexion = conectar_db()

    caso = conexion.execute(
        "SELECT * FROM casos_prueba WHERE id = ?",
        (id,)
    ).fetchone()

    requisitos = conexion.execute("""
        SELECT
            requisitos.id,
            requisitos.codigo,
            requisitos.descripcion,
            proyectos.nombre AS proyecto
        FROM requisitos
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY proyectos.nombre, requisitos.codigo
    """).fetchall()

    if caso is None:
        conexion.close()
        return "Caso de prueba no encontrado", 404

    if request.method == "POST":
        requisito_id = request.form["requisito_id"]
        codigo = request.form["codigo"]
        objetivo = request.form["objetivo"]
        precondiciones = request.form["precondiciones"]
        pasos = request.form["pasos"]
        datos_entrada = request.form["datos_entrada"]
        resultado_esperado = request.form["resultado_esperado"]
        resultado_obtenido = request.form["resultado_obtenido"]
        estado = request.form["estado"]
        fecha_ejecucion = request.form["fecha_ejecucion"]
        ejecutor = request.form["ejecutor"]
        observaciones = request.form["observaciones"]

        conexion.execute("""
            UPDATE casos_prueba
            SET requisito_id = ?,
                codigo = ?,
                objetivo = ?,
                precondiciones = ?,
                pasos = ?,
                datos_entrada = ?,
                resultado_esperado = ?,
                resultado_obtenido = ?,
                estado = ?,
                fecha_ejecucion = ?,
                ejecutor = ?,
                observaciones = ?
            WHERE id = ?
        """, (
            requisito_id,
            codigo,
            objetivo,
            precondiciones,
            pasos,
            datos_entrada,
            resultado_esperado,
            resultado_obtenido,
            estado,
            fecha_ejecucion,
            ejecutor,
            observaciones,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_casos_prueba"))

    conexion.close()

    return render_template(
        "editar_caso_prueba.html",
        caso=caso,
        requisitos=requisitos
    )


@app.route("/casos-prueba/eliminar/<int:id>", methods=["POST"])
def eliminar_caso_prueba(id):
    conexion = conectar_db()

    conexion.execute(
        "DELETE FROM casos_prueba WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar_casos_prueba"))

@app.route("/defectos")
def listar_defectos():
    conexion = conectar_db()

    defectos = conexion.execute("""
        SELECT
            defectos.id,
            defectos.codigo,
            defectos.descripcion,
            defectos.severidad,
            defectos.responsable,
            defectos.estado,
            casos_prueba.codigo AS caso_prueba
        FROM defectos
        LEFT JOIN casos_prueba
            ON defectos.caso_prueba_id = casos_prueba.id
        ORDER BY defectos.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "defectos.html",
        defectos=defectos
    )
@app.route("/defectos/nuevo", methods=["GET", "POST"])
def nuevo_defecto():
    conexion = conectar_db()

    casos = conexion.execute("""
        SELECT
            casos_prueba.id,
            casos_prueba.codigo,
            requisitos.codigo AS requisito,
            proyectos.nombre AS proyecto
        FROM casos_prueba
        INNER JOIN requisitos
            ON casos_prueba.requisito_id = requisitos.id
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY proyectos.nombre, casos_prueba.codigo
    """).fetchall()

    if request.method == "POST":
        caso_prueba_id = request.form["caso_prueba_id"]
        codigo = request.form["codigo"]
        descripcion = request.form["descripcion"]
        pasos_reproducir = request.form["pasos_reproducir"]
        severidad = request.form["severidad"]
        responsable = request.form["responsable"]
        estado = request.form["estado"]
        evidencia = request.form["evidencia"]

        conexion.execute("""
            INSERT INTO defectos (
                caso_prueba_id,
                codigo,
                descripcion,
                pasos_reproducir,
                severidad,
                responsable,
                estado,
                evidencia
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            caso_prueba_id if caso_prueba_id else None,
            codigo,
            descripcion,
            pasos_reproducir,
            severidad,
            responsable,
            estado,
            evidencia
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_defectos"))

    conexion.close()

    return render_template(
        "nuevo_defecto.html",
        casos=casos
    )
@app.route("/defectos/editar/<int:id>", methods=["GET", "POST"])
def editar_defecto(id):
    conexion = conectar_db()

    defecto = conexion.execute(
        "SELECT * FROM defectos WHERE id = ?",
        (id,)
    ).fetchone()

    casos = conexion.execute("""
        SELECT
            casos_prueba.id,
            casos_prueba.codigo,
            requisitos.codigo AS requisito,
            proyectos.nombre AS proyecto
        FROM casos_prueba
        INNER JOIN requisitos
            ON casos_prueba.requisito_id = requisitos.id
        INNER JOIN proyectos
            ON requisitos.proyecto_id = proyectos.id
        ORDER BY proyectos.nombre, casos_prueba.codigo
    """).fetchall()

    if defecto is None:
        conexion.close()
        return "Defecto no encontrado", 404

    if request.method == "POST":
        caso_prueba_id = request.form["caso_prueba_id"]
        codigo = request.form["codigo"]
        descripcion = request.form["descripcion"]
        pasos_reproducir = request.form["pasos_reproducir"]
        severidad = request.form["severidad"]
        responsable = request.form["responsable"]
        estado = request.form["estado"]
        evidencia = request.form["evidencia"]

        conexion.execute("""
            UPDATE defectos
            SET caso_prueba_id = ?,
                codigo = ?,
                descripcion = ?,
                pasos_reproducir = ?,
                severidad = ?,
                responsable = ?,
                estado = ?,
                evidencia = ?
            WHERE id = ?
        """, (
            caso_prueba_id if caso_prueba_id else None,
            codigo,
            descripcion,
            pasos_reproducir,
            severidad,
            responsable,
            estado,
            evidencia,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_defectos"))

    conexion.close()

    return render_template(
        "editar_defecto.html",
        defecto=defecto,
        casos=casos
    )


@app.route("/defectos/eliminar/<int:id>", methods=["POST"])
def eliminar_defecto(id):
    conexion = conectar_db()

    conexion.execute(
        "DELETE FROM defectos WHERE id = ?",
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar_defectos"))
@app.route("/indicadores")
def indicadores():
    conexion = conectar_db()

    total_pruebas = conexion.execute("""
        SELECT COUNT(*) AS total
        FROM casos_prueba
        WHERE estado IN ('Aprobado', 'Fallido', 'Bloqueado')
    """).fetchone()["total"]

    pruebas_aprobadas = conexion.execute("""
        SELECT COUNT(*) AS total
        FROM casos_prueba
        WHERE estado = 'Aprobado'
    """).fetchone()["total"]

    total_requisitos = conexion.execute("""
        SELECT COUNT(*) AS total
        FROM requisitos
    """).fetchone()["total"]

    requisitos_verificados = conexion.execute("""
        SELECT COUNT(DISTINCT requisito_id) AS total
        FROM casos_prueba
        WHERE estado IN ('Aprobado', 'Fallido', 'Bloqueado')
    """).fetchone()["total"]

    total_defectos = conexion.execute("""
        SELECT COUNT(*) AS total
        FROM defectos
    """).fetchone()["total"]

    defectos_resueltos = conexion.execute("""
        SELECT COUNT(*) AS total
        FROM defectos
        WHERE estado = 'Resuelto'
    """).fetchone()["total"]

    defectos_por_severidad = conexion.execute("""
        SELECT severidad, COUNT(*) AS total
        FROM defectos
        WHERE estado != 'Resuelto'
        GROUP BY severidad
    """).fetchall()

    conexion.close()

    porcentaje_pruebas = (
        round((pruebas_aprobadas / total_pruebas) * 100, 2)
        if total_pruebas > 0 else 0
    )

    porcentaje_requisitos = (
        round((requisitos_verificados / total_requisitos) * 100, 2)
        if total_requisitos > 0 else 0
    )

    porcentaje_defectos = (
        round((defectos_resueltos / total_defectos) * 100, 2)
        if total_defectos > 0 else 0
    )

    return render_template(
        "indicadores.html",
        total_pruebas=total_pruebas,
        pruebas_aprobadas=pruebas_aprobadas,
        porcentaje_pruebas=porcentaje_pruebas,
        total_requisitos=total_requisitos,
        requisitos_verificados=requisitos_verificados,
        porcentaje_requisitos=porcentaje_requisitos,
        total_defectos=total_defectos,
        defectos_resueltos=defectos_resueltos,
        porcentaje_defectos=porcentaje_defectos,
        defectos_por_severidad=defectos_por_severidad
    )
@app.route("/evaluacion")
def listar_evaluaciones():
    conexion = conectar_db()

    evaluaciones = conexion.execute("""
        SELECT
            evaluaciones_calidad.id,
            evaluaciones_calidad.caracteristica,
            evaluaciones_calidad.criterio,
            evaluaciones_calidad.metodo_medicion,
            evaluaciones_calidad.resultado,
            evaluaciones_calidad.porcentaje,
            evaluaciones_calidad.evidencia,
            evaluaciones_calidad.observaciones,
            proyectos.nombre AS proyecto
        FROM evaluaciones_calidad
        INNER JOIN proyectos
            ON evaluaciones_calidad.proyecto_id = proyectos.id
        ORDER BY evaluaciones_calidad.id DESC
    """).fetchall()

    conexion.close()

    return render_template(
        "evaluacion.html",
        evaluaciones=evaluaciones
    )


@app.route("/evaluacion/nueva", methods=["GET", "POST"])
def nueva_evaluacion():
    conexion = conectar_db()

    proyectos = conexion.execute(
        "SELECT id, nombre FROM proyectos ORDER BY nombre"
    ).fetchall()

    if request.method == "POST":
        proyecto_id = request.form["proyecto_id"]
        caracteristica = request.form["caracteristica"]
        criterio = request.form["criterio"]
        metodo_medicion = request.form["metodo_medicion"]
        resultado = request.form["resultado"]
        porcentaje = request.form["porcentaje"]
        evidencia = request.form["evidencia"]
        observaciones = request.form["observaciones"]

        conexion.execute("""
            INSERT INTO evaluaciones_calidad (
                proyecto_id,
                caracteristica,
                criterio,
                metodo_medicion,
                resultado,
                porcentaje,
                evidencia,
                observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proyecto_id,
            caracteristica,
            criterio,
            metodo_medicion,
            resultado,
            porcentaje if porcentaje else None,
            evidencia,
            observaciones
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_evaluaciones"))

    conexion.close()

    return render_template(
        "nueva_evaluacion.html",
        proyectos=proyectos
    )

@app.route("/evaluacion/editar/<int:id>", methods=["GET", "POST"])
def editar_evaluacion(id):

    conexion = conectar_db()

    evaluacion = conexion.execute(
        """
        SELECT *
        FROM evaluaciones_calidad
        WHERE id = ?
        """,
        (id,)
    ).fetchone()

    proyectos = conexion.execute(
        """
        SELECT id, nombre
        FROM proyectos
        ORDER BY nombre
        """
    ).fetchall()

    if evaluacion is None:
        conexion.close()
        return "Evaluación no encontrada", 404

    if request.method == "POST":

        proyecto_id = request.form["proyecto_id"]
        caracteristica = request.form["caracteristica"]
        criterio = request.form["criterio"]
        metodo_medicion = request.form["metodo_medicion"]
        resultado = request.form["resultado"]
        porcentaje = request.form["porcentaje"]
        evidencia = request.form["evidencia"]
        observaciones = request.form["observaciones"]

        conexion.execute("""
            UPDATE evaluaciones_calidad

            SET proyecto_id = ?,
                caracteristica = ?,
                criterio = ?,
                metodo_medicion = ?,
                resultado = ?,
                porcentaje = ?,
                evidencia = ?,
                observaciones = ?

            WHERE id = ?
        """, (
            proyecto_id,
            caracteristica,
            criterio,
            metodo_medicion,
            resultado,
            porcentaje if porcentaje else None,
            evidencia,
            observaciones,
            id
        ))

        conexion.commit()
        conexion.close()

        return redirect(url_for("listar_evaluaciones"))

    conexion.close()

    return render_template(
        "editar_evaluacion.html",
        evaluacion=evaluacion,
        proyectos=proyectos
    )
@app.route("/evaluacion/eliminar/<int:id>", methods=["POST"])
def eliminar_evaluacion(id):

    conexion = conectar_db()

    conexion.execute(
        """
        DELETE FROM evaluaciones_calidad
        WHERE id = ?
        """,
        (id,)
    )

    conexion.commit()
    conexion.close()

    return redirect(url_for("listar_evaluaciones"))
@app.route("/informe")
def informe():

    conexion = conectar_db()

    # =========================
    # PROYECTOS
    # =========================

    proyectos = conexion.execute("""
        SELECT id, nombre
        FROM proyectos
        ORDER BY nombre
    """).fetchall()

    proyecto_id = request.args.get(
        "proyecto_id",
        type=int
    )

    # Si no se ha seleccionado proyecto,
    # toma el primero disponible
    if proyecto_id is None and proyectos:
        proyecto_id = proyectos[0]["id"]

    proyecto = None

    # =========================
    # VALORES POR DEFECTO
    # =========================

    total_requisitos = 0
    requisitos_verificados = 0
    porcentaje_requisitos = 0

    total_pruebas = 0
    pruebas_ejecutadas = 0
    pruebas_aprobadas = 0
    pruebas_fallidas = 0
    pruebas_bloqueadas = 0
    porcentaje_pruebas = 0

    total_defectos = 0
    defectos_resueltos = 0
    defectos_pendientes = 0
    porcentaje_defectos = 0

    defectos_por_severidad = []

    evaluaciones = []
    promedio_evaluacion = 0

    cumplimiento_general = 0
    estado_general = "Sin información"

    indicadores_disponibles = []

    # =========================
    # SI EXISTE PROYECTO
    # =========================

    if proyecto_id:

        proyecto = conexion.execute("""
            SELECT *
            FROM proyectos
            WHERE id = ?
        """, (
            proyecto_id,
        )).fetchone()

        # =========================
        # REQUISITOS
        # =========================

        total_requisitos = conexion.execute("""
            SELECT COUNT(*) AS total
            FROM requisitos
            WHERE proyecto_id = ?
        """, (
            proyecto_id,
        )).fetchone()["total"]

        requisitos_verificados = conexion.execute("""
            SELECT
                COUNT(
                    DISTINCT casos_prueba.requisito_id
                ) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?

            AND casos_prueba.estado IN (
                'Aprobado',
                'Fallido',
                'Bloqueado'
            )
        """, (
            proyecto_id,
        )).fetchone()["total"]

        if total_requisitos > 0:

            porcentaje_requisitos = round(
                (
                    requisitos_verificados
                    / total_requisitos
                ) * 100,
                2
            )

            indicadores_disponibles.append(
                porcentaje_requisitos
            )

        # =========================
        # CASOS DE PRUEBA
        # =========================

        total_pruebas = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
        """, (
            proyecto_id,
        )).fetchone()["total"]

        pruebas_ejecutadas = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?

            AND casos_prueba.estado IN (
                'Aprobado',
                'Fallido',
                'Bloqueado'
            )
        """, (
            proyecto_id,
        )).fetchone()["total"]

        pruebas_aprobadas = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
            AND casos_prueba.estado = 'Aprobado'
        """, (
            proyecto_id,
        )).fetchone()["total"]

        pruebas_fallidas = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
            AND casos_prueba.estado = 'Fallido'
        """, (
            proyecto_id,
        )).fetchone()["total"]

        pruebas_bloqueadas = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM casos_prueba

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
            AND casos_prueba.estado = 'Bloqueado'
        """, (
            proyecto_id,
        )).fetchone()["total"]

        if pruebas_ejecutadas > 0:

            porcentaje_pruebas = round(
                (
                    pruebas_aprobadas
                    / pruebas_ejecutadas
                ) * 100,
                2
            )

            indicadores_disponibles.append(
                porcentaje_pruebas
            )

        # =========================
        # DEFECTOS
        # =========================

        total_defectos = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM defectos

            INNER JOIN casos_prueba
                ON defectos.caso_prueba_id =
                   casos_prueba.id

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
        """, (
            proyecto_id,
        )).fetchone()["total"]

        defectos_resueltos = conexion.execute("""
            SELECT COUNT(*) AS total

            FROM defectos

            INNER JOIN casos_prueba
                ON defectos.caso_prueba_id =
                   casos_prueba.id

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
            AND defectos.estado = 'Resuelto'
        """, (
            proyecto_id,
        )).fetchone()["total"]

        defectos_pendientes = (
            total_defectos
            - defectos_resueltos
        )

        if total_defectos > 0:

            porcentaje_defectos = round(
                (
                    defectos_resueltos
                    / total_defectos
                ) * 100,
                2
            )

            indicadores_disponibles.append(
                porcentaje_defectos
            )

        defectos_por_severidad = conexion.execute("""
            SELECT
                defectos.severidad,
                COUNT(*) AS total

            FROM defectos

            INNER JOIN casos_prueba
                ON defectos.caso_prueba_id =
                   casos_prueba.id

            INNER JOIN requisitos
                ON casos_prueba.requisito_id =
                   requisitos.id

            WHERE requisitos.proyecto_id = ?
            AND defectos.estado != 'Resuelto'

            GROUP BY defectos.severidad

            ORDER BY defectos.severidad
        """, (
            proyecto_id,
        )).fetchall()

        # =========================
        # EVALUACIÓN ISO/IEC 25010
        # =========================

        evaluaciones = conexion.execute("""
            SELECT *
            FROM evaluaciones_calidad

            WHERE proyecto_id = ?

            ORDER BY caracteristica
        """, (
            proyecto_id,
        )).fetchall()

        promedio = conexion.execute("""
            SELECT
                AVG(porcentaje) AS promedio

            FROM evaluaciones_calidad

            WHERE proyecto_id = ?
            AND porcentaje IS NOT NULL
        """, (
            proyecto_id,
        )).fetchone()["promedio"]

        if promedio is not None:

            promedio_evaluacion = round(
                promedio,
                2
            )

            indicadores_disponibles.append(
                promedio_evaluacion
            )

        # =========================
        # CUMPLIMIENTO GENERAL
        # =========================

        if indicadores_disponibles:

            cumplimiento_general = round(
                sum(indicadores_disponibles)
                / len(indicadores_disponibles),
                2
            )

        # =========================
        # ESTADO GENERAL
        # =========================

        if not indicadores_disponibles:

            estado_general = "Sin información"

        elif cumplimiento_general >= 80:

            estado_general = "Cumple"

        elif cumplimiento_general >= 60:

            estado_general = "Cumple parcialmente"

        else:

            estado_general = "No cumple"

    conexion.close()

    return render_template(
        "informe.html",

        proyectos=proyectos,
        proyecto_id=proyecto_id,
        proyecto=proyecto,

        total_requisitos=total_requisitos,
        requisitos_verificados=requisitos_verificados,
        porcentaje_requisitos=porcentaje_requisitos,

        total_pruebas=total_pruebas,
        pruebas_ejecutadas=pruebas_ejecutadas,
        pruebas_aprobadas=pruebas_aprobadas,
        pruebas_fallidas=pruebas_fallidas,
        pruebas_bloqueadas=pruebas_bloqueadas,
        porcentaje_pruebas=porcentaje_pruebas,

        total_defectos=total_defectos,
        defectos_resueltos=defectos_resueltos,
        defectos_pendientes=defectos_pendientes,
        porcentaje_defectos=porcentaje_defectos,
        defectos_por_severidad=defectos_por_severidad,

        evaluaciones=evaluaciones,
        promedio_evaluacion=promedio_evaluacion,

        cumplimiento_general=cumplimiento_general,
        estado_general=estado_general
    )

if __name__ == "__main__":
    crear_base_datos()
    app.run(debug=True)