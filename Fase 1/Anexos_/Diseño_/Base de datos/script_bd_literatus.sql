-- =============================================================================
-- PROYECTO: LITERATUS TRISKELE
-- ESQUEMA DE BASE DE DATOS EN POSTGRESQL
-- =============================================================================

-- -----------------------------------------------------------------------------
-- TABLA: USUARIO
-- -----------------------------------------------------------------------------
CREATE TABLE USUARIO (
    id_usuario          BIGSERIAL PRIMARY KEY,
    rut                 VARCHAR(12) UNIQUE NOT NULL,
    nombre_usuario      VARCHAR(50) UNIQUE NOT NULL,
    correo_electronico  VARCHAR(100) UNIQUE NOT NULL,
    contrasena          VARCHAR(255) NOT NULL,
    rol                 VARCHAR(20) NOT NULL CHECK (rol IN ('ESTUDIANTE', 'DOCENTE', 'ADMIN')),
    nivel_exp           INTEGER NOT NULL DEFAULT 0,
    fecha_registro      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------------------------------------------------------------
-- TABLA: LIBRO
-- -----------------------------------------------------------------------------
CREATE TABLE LIBRO (
    id_libro            SERIAL PRIMARY KEY,
    titulo              VARCHAR(150) NOT NULL,
    autor               VARCHAR(100) NOT NULL,
    isbn                VARCHAR(20) UNIQUE,
    archivo_epub        VARCHAR(255) NOT NULL,
    total_capitulos     INTEGER NOT NULL CHECK (total_capitulos > 0)
);

-- -----------------------------------------------------------------------------
-- TABLA: CAPITULO
-- -----------------------------------------------------------------------------
CREATE TABLE CAPITULO (
    id_capitulo         SERIAL PRIMARY KEY,
    id_libro            INTEGER NOT NULL,
    numero_capitulo     INTEGER NOT NULL,
    titulo_capitulo     VARCHAR(150) NOT NULL,
    CONSTRAINT Capitulo_Libro_FK FOREIGN KEY (id_libro) REFERENCES LIBRO(id_libro) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: PROGRESO_LECTURA
-- -----------------------------------------------------------------------------
CREATE TABLE PROGRESO_LECTURA (
    id_progreso         BIGSERIAL PRIMARY KEY,
    id_usuario          BIGINT NOT NULL,
    id_libro            INTEGER NOT NULL,
    ultimo_capitulo     INTEGER NOT NULL DEFAULT 1,
    porcentaje_avance   NUMERIC(5,2) NOT NULL DEFAULT 0.00 CHECK (porcentaje_avance BETWEEN 0 AND 100),
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT Progreso_Usuario_FK FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    CONSTRAINT Progreso_Libro_FK FOREIGN KEY (id_libro) REFERENCES LIBRO(id_libro) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: GLOSARIO
-- -----------------------------------------------------------------------------
CREATE TABLE GLOSARIO (
    id_glosario         SERIAL PRIMARY KEY,
    id_libro            INTEGER NOT NULL,
    termino             VARCHAR(100) NOT NULL,
    definicion          TEXT NOT NULL,
    CONSTRAINT Glosario_Libro_FK FOREIGN KEY (id_libro) REFERENCES LIBRO(id_libro) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: CHAT_TUTOR_IA (Integración LLM / Guardrails)
-- -----------------------------------------------------------------------------
CREATE TABLE CHAT_TUTOR_IA (
    id_chat             BIGSERIAL PRIMARY KEY,
    id_usuario          BIGINT NOT NULL,
    id_libro            INTEGER NOT NULL,
    capitulo_actual     INTEGER NOT NULL,
    mensaje_usuario     TEXT NOT NULL,
    respuesta_ia        TEXT NOT NULL,
    fecha_interaccion   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT Chat_Usuario_FK FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    CONSTRAINT Chat_Libro_FK FOREIGN KEY (id_libro) REFERENCES LIBRO(id_libro) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: DESAFIO_JEFE (Evaluación del Modo Jefe)
-- -----------------------------------------------------------------------------
CREATE TABLE DESAFIO_JEFE (
    id_desafio          BIGSERIAL PRIMARY KEY,
    id_usuario          BIGINT NOT NULL,
    id_capitulo         INTEGER NOT NULL,
    respuesta_alumno    TEXT NOT NULL,
    puntaje_literal     INTEGER NOT NULL CHECK (puntaje_literal BETWEEN 0 AND 100),
    puntaje_inferencial INTEGER NOT NULL CHECK (puntaje_inferencial BETWEEN 0 AND 100),
    puntaje_critico     INTEGER NOT NULL CHECK (puntaje_critico BETWEEN 0 AND 100),
    feedback_ia         TEXT NOT NULL,
    estado_aprobacion   VARCHAR(20) NOT NULL CHECK (estado_aprobacion IN ('APROBADO', 'RECHAZADO')),
    CONSTRAINT Desafio_Usuario_FK FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    CONSTRAINT Desafio_Capitulo_FK FOREIGN KEY (id_capitulo) REFERENCES CAPITULO(id_capitulo) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: NODO_DECISION (Mapa Narrativo Causal)
-- -----------------------------------------------------------------------------
CREATE TABLE NODO_DECISION (
    id_nodo             SERIAL PRIMARY KEY,
    id_libro            INTEGER NOT NULL,
    codigo_nodo         VARCHAR(50) NOT NULL,
    descripcion_nodo    TEXT NOT NULL,
    CONSTRAINT Nodo_Libro_FK FOREIGN KEY (id_libro) REFERENCES LIBRO(id_libro) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: REGISTRO_DECISION_USUARIO
-- -----------------------------------------------------------------------------
CREATE TABLE REGISTRO_DECISION_USUARIO (
    id_registro_decision BIGSERIAL PRIMARY KEY,
    id_usuario           BIGINT NOT NULL,
    id_nodo              INTEGER NOT NULL,
    opcion_elegida       VARCHAR(100) NOT NULL,
    fecha_decision       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT RegDecision_Usuario_FK FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    CONSTRAINT RegDecision_Nodo_FK FOREIGN KEY (id_nodo) REFERENCES NODO_DECISION(id_nodo) ON DELETE CASCADE
);

-- -----------------------------------------------------------------------------
-- TABLA: INVENTARIO_RECOMPENSA (Gamificación)
-- -----------------------------------------------------------------------------
CREATE TABLE INVENTARIO_RECOMPENSA (
    id_inventario       BIGSERIAL PRIMARY KEY,
    id_usuario          BIGINT NOT NULL,
    nombre_item         VARCHAR(100) NOT NULL,
    tipo_item           VARCHAR(50) NOT NULL CHECK (tipo_item IN ('MEDALLA', 'INSIGNIA', 'OBJETO')),
    fecha_obtencion     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT Inventario_Usuario_FK FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario) ON DELETE CASCADE
);

-- =============================================================================
-- PRUEBAS / DATOS DE POBLAMIENTO INICIAL (TESTING)
-- =============================================================================

INSERT INTO USUARIO (rut, nombre_usuario, correo_electronico, contrasena, rol, nivel_exp) 
VALUES ('19133540-6', 'elopez', 'enzo.lopez@alumnos.duoc.cl', '$2a$12$eImiTXuWVxfM37uY4JANjO', 'ESTUDIANTE', 150);

INSERT INTO USUARIO (rut, nombre_usuario, correo_electronico, contrasena, rol, nivel_exp) 
VALUES ('19512887-1', 'lmerino', 'laura.merino@alumnos.duoc.cl', '$2a$12$eImiTXuWVxfM37uY4JANjO', 'DOCENTE', 0);

INSERT INTO LIBRO (titulo, autor, isbn, archivo_epub, total_capitulos) 
VALUES ('El Principito', 'Antoine de Saint-Exupéry', '978-0156013987', '/epubs/el_principito.epub', 27);

INSERT INTO CAPITULO (id_libro, numero_capitulo, titulo_capitulo) 
VALUES (1, 1, 'Capítulo I: El dibujo de la boa');

INSERT INTO PROGRESO_LECTURA (id_usuario, id_libro, ultimo_capitulo, porcentaje_avance) 
VALUES (1, 1, 1, 3.70);

INSERT INTO GLOSARIO (id_libro, termino, definicion) 
VALUES (1, 'Boa', 'Serpiente de gran tamaño que mata a sus presas sofocándolas.');

INSERT INTO CHAT_TUTOR_IA (id_usuario, id_libro, capitulo_actual, mensaje_usuario, respuesta_ia) 
VALUES (1, 1, 1, '¿Por qué los adultos no entendieron el dibujo?', 'Los adultos confundieron el dibujo con un sombrero porque han perdido la imaginación infantil.');

INSERT INTO DESAFIO_JEFE (id_usuario, id_capitulo, respuesta_alumno, puntaje_literal, puntaje_inferencial, puntaje_critico, feedback_ia, estado_aprobacion) 
VALUES (1, 1, 'El autor dibujó una boa comiendo un elefante, pero los adultos vieron un sombrero.', 100, 90, 85, 'Excelente análisis. Demuestras clara comprensión del mensaje inicial.', 'APROBADO');

INSERT INTO INVENTARIO_RECOMPENSA (id_usuario, nombre_item, tipo_item) 
VALUES (1, 'Insignia Primer Capitulo', 'INSIGNIA');

