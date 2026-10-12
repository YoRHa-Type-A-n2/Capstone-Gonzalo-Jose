# Literatus (Ecosistema Triskele) 📚⚔️
> Plataforma web interactiva de fortalecimiento cognitivo y comprensión lectora basada en dinámicas de juego RPG y debate dialéctico con Inteligencia Artificial.

[![Status](https://img.shields.io/badge/Status-Fase%201%20(Planificación)-blue)]()
[![Stack](https://img.shields.io/badge/Stack-Angular18%20|%20DjangoREST%20|%20PostgreSQL-teal)]()
[![AI-Engine](https://img.shields.io/badge/IA-Gemini%202.0%20|%20DeepSeek-purple)]()

---

## 1. Problemática
En Chile, los resultados del SIMCE evidencian una severa brecha en comprensión lectora: el 48% de los estudiantes de 2° medio presenta un nivel insuficiente. Este fenómeno se ve agravado por dos factores:
- **Lectura Pasiva:** Bibliotecas digitales reducidas a PDFs planos que desmotivan al alumnado.
- **Evaluación de Memoria Explícita:** Pruebas tradicionales basadas en retención puntual que no fomentan el análisis inferencial ni el juicio crítico.

## 2. Nuestra Solución: Lectura Gamificada (RPG de Comprensión)
Literatus convierte la comprensión lectora en la mecánica motriz del avance:
- **Core Loop:** Explorar ➔ Leer (EPUB + TTS) ➔ Conversar con Personajes ➔ Superar Desafíos / Jefes ➔ Ganar XP y Estrellas (⭐) ➔ Desbloquear Objetos ➔ Tomar Decisiones ➔ Descubrir Nuevas Rutas / Releer.
- **Regla Curricular:** El contenido obligatorio del plan escolar nunca se bloquea. Los objetos y afinidades desbloquean rutas secundarias, dilemas éticos y finales alternativos.

## 3. Módulos Principales
1. **Lector Inmersivo & Audio-Sync:** Visor EPUB adaptativo por ciclo (4°-5° básico visual / 6°-2° medio analítico) con narración por voz asistida (TTS karaoke sincronizado).
2. **Motor Dialéctico con Personajes:** Chat contextual en escena mediante IA sujeta a guardrails pedagógicos estrictos (anti-spoilers y restricción de contexto de obra).
3. **Mecánicas RPG y Desafíos de Comprensión:** Evaluación al cierre de cada capítulo ("Jefes de Comprensión"), progresión por XP/niveles, inventario de objetos y clases de lector (Detective, Sabio, Explorador, Diplomático).
4. **Reportería y Analítica Docente:**
   - **Ficha Pedagógica Individual (PDF):** Generada programáticamente con ReportLab con rúbrica cognitiva (literal, inferencial, crítico).
   - **Sábana Consolidada de Curso (Excel/CSV):** Exportada con OpenPyXL/Pandas con semaforización de alertas de rezago.

## 4. Arquitectura Tecnológica Tentativa
- **Frontend:** Angular 18 (SPA responsiva, Epub.js, Web Audio API).
- **Backend:** Python + Django REST Framework (API RESTful, JWT con refresh token).
- **Base de Datos:** PostgreSQL (modelo relacional de usuarios, progreso, inventario y métricas).
- **IA y Voz:** Google Gemini API / DeepSeek (LLM con guardrails), Web Speech API / Piper TTS.
- **Generación de Reportes:** ReportLab (PDF) y OpenPyXL / Pandas (.xlsx / .csv).

## 5. Equipo de Proyecto (Duoc UC - Capstone)
- **José Ignacio Muñoz Herrera**
- **Gonzalo Esteban Venegas**
- **Docente Guía:** Arturo Alex Vargas Reyes
- **Cliente Asociado:** Triskel edu
