import pandas as pd
import numpy as np


class LinkedInAnalyzer:
    """
    Analizador de los datos exportados por LinkedIn Creator Analytics.

    IMPORTANTE:
    - PUBLICACIONES PRINCIPALES contiene DOS listados independientes:
      uno ordenado por interacciones y otro por impresiones.
    - LinkedIn indica que esa lista puede incluir como máximo 50 publicaciones.
    - INTERACCIÓN contiene la serie diaria del periodo solicitado (7/14/28/90/365 días).

    Por tanto, nunca se debe utilizar PUBLICACIONES PRINCIPALES para deducir
    la duración del periodo histórico ni la frecuencia real de publicación.
    """

    def __init__(self, dataframe, interaccion_dataframe=None):
        self.df_original = dataframe.copy()
        self.df = self._limpiar_dataframe()

        self.df_interaccion_original = (
            interaccion_dataframe.copy()
            if interaccion_dataframe is not None
            else pd.DataFrame()
        )
        self.df_interaccion = self._limpiar_interaccion()

        self._publicaciones_cache = None

    # ======================================================
    # PERIODO HISTÓRICO REAL
    # ======================================================
    def obtener_periodo(self):
        """
        Devuelve el periodo REAL del informe usando INTERACCIÓN.

        No usa las fechas de PUBLICACIONES PRINCIPALES porque esa tabla está
        limitada a un máximo de 50 registros y sus dos bloques son rankings,
        no un histórico completo.
        """
        if not self.df_interaccion.empty:
            columna_fecha = self.buscar_columna_interaccion([
                "Fecha",
                "Date"
            ])

            if columna_fecha:
                fechas = pd.to_datetime(
                    self.df_interaccion[columna_fecha],
                    errors="coerce",
                    dayfirst=True
                ).dropna().sort_values()

                if not fechas.empty:
                    return (
                        fechas.min().strftime("%d/%m/%Y"),
                        fechas.max().strftime("%d/%m/%Y")
                    )

        # Compatibilidad de respaldo si no se suministró INTERACCIÓN.
        posibles = [
            "Fecha",
            "Fecha de publicación",
            "Fecha de creación",
            "Fecha de publicación del contenido",
            "Date",
            "Published date",
            "Publication date",
            "Publish date",
            "Created date",
            "Creation date"
        ]

        columna = self.buscar_columna(posibles)
        if columna is None:
            return None

        fechas = pd.to_datetime(
            self.df[columna],
            errors="coerce",
            dayfirst=True
        ).dropna()

        if fechas.empty:
            return None

        return (
            fechas.min().strftime("%d/%m/%Y"),
            fechas.max().strftime("%d/%m/%Y")
        )

    # ======================================================
    # LIMPIEZA DE PUBLICACIONES
    # ======================================================
    def _limpiar_dataframe(self):
        df = self.df_original.copy()

        df = df.dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]

        return df

    # ======================================================
    # LIMPIEZA DE INTERACCIÓN
    # ======================================================
    def _limpiar_interaccion(self):
        if self.df_interaccion_original.empty:
            return pd.DataFrame()

        df = self.df_interaccion_original.copy()
        df.columns = [str(c).strip() for c in df.columns]
        return df

    # ======================================================
    # BUSCAR COLUMNAS EN PUBLICACIONES
    # ======================================================
    def buscar_columna(self, posibles):
        for nombre in posibles:
            if nombre in self.df.columns:
                return nombre
        return None

    # ======================================================
    # BUSCAR COLUMNAS EN INTERACCIÓN
    # ======================================================
    def buscar_columna_interaccion(self, posibles):
        for nombre in posibles:
            if nombre in self.df_interaccion.columns:
                return nombre
        return None

    # ======================================================
    # BUSCAR COLUMNAS DUPLICADAS DE LINKEDIN
    # ======================================================
    def _columnas_prefijo(self, nombre_base):
        """
        Encuentra columnas como:
        - 'URL de la publicación'
        - 'URL de la publicación.1'

        Pandas añade '.1', '.2', etc. cuando encuentra cabeceras duplicadas.
        """
        columnas = []
        for col in self.df.columns:
            if col == nombre_base or col.startswith(nombre_base + "."):
                columnas.append(col)
        return columnas

    # ======================================================
    # NORMALIZAR LAS DOS TABLAS LATERALES DE LINKEDIN
    # ======================================================
    def obtener_publicaciones(self):
        """
        Une los dos rankings independientes de PUBLICACIONES PRINCIPALES:

        BLOQUE A-C:
            URL | Fecha | Interacciones

        BLOQUE E-G:
            URL | Fecha | Impresiones

        Se fusionan por URL y se eliminan duplicados.
        """
        if self._publicaciones_cache is not None:
            return self._publicaciones_cache

        urls = self._columnas_prefijo("URL de la publicación")
        fechas = self._columnas_prefijo("Fecha de publicación")

        # Fallback para versiones en inglés.
        if not urls:
            urls = self._columnas_prefijo("URL")
        if not fechas:
            fechas = self._columnas_prefijo("Fecha")

        if not urls:
            return []

        # En la exportación conocida de LinkedIn:
        # urls[0] = bloque de interacciones
        # urls[1] = bloque de impresiones
        url_interacciones = urls[0]
        url_impresiones = urls[1] if len(urls) > 1 else None

        fecha_interacciones = fechas[0] if fechas else None
        fecha_impresiones = fechas[1] if len(fechas) > 1 else None

        columnas_interacciones = self._columnas_prefijo("Interacciones")
        if not columnas_interacciones:
            columnas_interacciones = self._columnas_prefijo("Interactions")
        columna_interacciones = (
            columnas_interacciones[0]
            if columnas_interacciones
            else None
        )

        columnas_impresiones = self._columnas_prefijo("Impresiones")
        if not columnas_impresiones:
            columnas_impresiones = self._columnas_prefijo("Impressions")
        columna_impresiones = (
            columnas_impresiones[0]
            if columnas_impresiones
            else None
        )

        registros = {}

        def asegurar(url):
            url = str(url).strip()
            if url not in registros:
                registros[url] = {"URL": url}
            return registros[url]

        for _, fila in self.df.iterrows():
            # ----------------------------------------------
            # BLOQUE A-C: INTERACCIONES
            # ----------------------------------------------
            if url_interacciones:
                url = fila.get(url_interacciones)
                if pd.notna(url) and str(url).strip():
                    publicacion = asegurar(url)

                    if fecha_interacciones:
                        fecha = pd.to_datetime(
                            fila.get(fecha_interacciones),
                            errors="coerce",
                            dayfirst=True
                        )
                        if pd.notna(fecha):
                            publicacion["Fecha"] = fecha.strftime("%d/%m/%Y")

                    if columna_interacciones:
                        interacciones = pd.to_numeric(
                            fila.get(columna_interacciones),
                            errors="coerce"
                        )
                        if pd.notna(interacciones):
                            publicacion["Interacciones"] = int(interacciones)

            # ----------------------------------------------
            # BLOQUE E-G: IMPRESIONES
            # ----------------------------------------------
            if url_impresiones:
                url = fila.get(url_impresiones)
                if pd.notna(url) and str(url).strip():
                    publicacion = asegurar(url)

                    if fecha_impresiones:
                        fecha = pd.to_datetime(
                            fila.get(fecha_impresiones),
                            errors="coerce",
                            dayfirst=True
                        )
                        if pd.notna(fecha):
                            # Si no existe fecha en el otro bloque, usamos esta.
                            publicacion.setdefault(
                                "Fecha",
                                fecha.strftime("%d/%m/%Y")
                            )

                    if columna_impresiones:
                        impresiones = pd.to_numeric(
                            fila.get(columna_impresiones),
                            errors="coerce"
                        )
                        if pd.notna(impresiones):
                            publicacion["Impresiones"] = int(impresiones)

        publicaciones = list(registros.values())

        # Engagement calculado solo cuando existen ambos datos.
        for publicacion in publicaciones:
            impresiones = publicacion.get("Impresiones")
            interacciones = publicacion.get("Interacciones")

            if impresiones is not None and impresiones > 0 and interacciones is not None:
                publicacion["Engagement"] = round(
                    (interacciones / impresiones) * 100,
                    2
                )

        self._publicaciones_cache = publicaciones
        return publicaciones

    # ======================================================
    # DATOS HISTÓRICOS DIARIOS
    # ======================================================

    def metricas_historicas(self):
        """
        Métricas que sí representan el periodo completo exportado por LinkedIn.
        Se obtienen de INTERACCIÓN, no de PUBLICACIONES PRINCIPALES.
        """
        estadisticas = {}

        if self.df_interaccion.empty:
            return estadisticas

        columna_fecha = self.buscar_columna_interaccion(["Fecha", "Date"])
        columna_impresiones = self.buscar_columna_interaccion([
            "Impresiones",
            "Impressions"
        ])
        columna_interacciones = self.buscar_columna_interaccion([
            "Interacciones",
            "Interactions"
        ])

        if columna_fecha:
            fechas = pd.to_datetime(
                self.df_interaccion[columna_fecha],
                errors="coerce",
                dayfirst=True
            )
            fechas_validas = fechas.dropna().sort_values()

            if not fechas_validas.empty:
                estadisticas["Días del histórico exportado"] = int(
                    (fechas_validas.max() - fechas_validas.min()).days + 1
                )
                estadisticas["Fecha inicio del histórico"] = fechas_validas.min().strftime("%d/%m/%Y")
                estadisticas["Fecha fin del histórico"] = fechas_validas.max().strftime("%d/%m/%Y")

        if columna_impresiones:
            serie = pd.to_numeric(
                self.df_interaccion[columna_impresiones],
                errors="coerce"
            ).fillna(0)
            estadisticas["Impresiones acumuladas del periodo"] = int(serie.sum())
            estadisticas["Días con impresiones"] = int((serie > 0).sum())
            estadisticas["Máximo de impresiones en un día"] = int(serie.max())

        if columna_interacciones:
            serie = pd.to_numeric(
                self.df_interaccion[columna_interacciones],
                errors="coerce"
            ).fillna(0)
            estadisticas["Interacciones acumuladas del periodo"] = int(serie.sum())
            estadisticas["Días con interacciones"] = int((serie > 0).sum())

        return estadisticas

    # ======================================================
    # PUBLICACIONES DESTACADAS
    # ======================================================
    def publicaciones_destacadas(self):

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {
                "Top 5": [],
                "Bottom 5": [],
                "Top 5 Engagement": []
            }

        publicaciones_con_impresiones = [
            p for p in publicaciones
            if p.get("Impresiones") is not None
        ]

        top_5 = sorted(
            publicaciones_con_impresiones,
            key=lambda p: p.get("Impresiones", 0),
            reverse=True
        )[:5]

        bottom_5 = sorted(
            publicaciones_con_impresiones,
            key=lambda p: p.get("Impresiones", 0)
        )[:5]

        publicaciones_con_engagement = [
            p for p in publicaciones
            if p.get("Engagement") is not None
        ]

        top_engagement = sorted(
            publicaciones_con_engagement,
            key=lambda p: p.get("Engagement", 0),
            reverse=True
        )[:5]

        return {
            "Top 5": top_5,
            "Bottom 5": bottom_5,
            "Top 5 Engagement": top_engagement
        }


    # ======================================================
    # DATOS DE REFERENCIA PARA VALIDACIÓN DE LA IA
    # ======================================================
    def datos_validacion(self):

        return {
            "metricas": self.metricas(),
            "periodo": self.obtener_periodo(),
            "publicaciones_destacadas": self.publicaciones_destacadas()
        }


    # ======================================================
    # ANÁLISIS DE RENDIMIENTO
    # ======================================================

    def analisis_rendimiento(self):
        publicaciones = self.obtener_publicaciones()

        publicaciones_validas = [
            p for p in publicaciones
            if p.get("Impresiones") is not None
        ]

        if not publicaciones_validas:
            return {}

        impresiones = [p["Impresiones"] for p in publicaciones_validas]
        media = sum(impresiones) / len(impresiones)
        mediana = float(np.median(impresiones))

        sobre_media = [p for p in publicaciones_validas if p["Impresiones"] > media]
        bajo_media = [p for p in publicaciones_validas if p["Impresiones"] < media]

        analisis = {
            "Publicaciones con impresiones": len(publicaciones_validas),
            "Media de impresiones de publicaciones disponibles": round(media, 1),
            "Mediana de impresiones de publicaciones disponibles": round(mediana, 1),
            "Publicaciones sobre la media": len(sobre_media),
            "Porcentaje sobre la media": round(len(sobre_media) / len(publicaciones_validas) * 100, 1),
            "Publicaciones bajo la media": len(bajo_media),
            "Porcentaje bajo la media": round(len(bajo_media) / len(publicaciones_validas) * 100, 1),
            "Diferencia media-mediana": round(media - mediana, 1),
            "Ratio media/mediana": round(media / mediana, 2) if mediana > 0 else 0,
        }

        mejor_alcance = max(
            publicaciones_validas,
            key=lambda p: p["Impresiones"]
        )
        analisis["Mayor alcance"] = mejor_alcance["Impresiones"]
        analisis["Interacciones mayor alcance"] = mejor_alcance.get("Interacciones", 0)
        analisis["Engagement mayor alcance"] = mejor_alcance.get("Engagement", 0)
        analisis["Fecha mayor alcance"] = mejor_alcance.get("Fecha", "N/D")

        publicaciones_con_engagement = [
            p for p in publicaciones_validas
            if p.get("Engagement") is not None
        ]

        if publicaciones_con_engagement:
            mejor_engagement = max(
                publicaciones_con_engagement,
                key=lambda p: p.get("Engagement", 0)
            )
            analisis["Mejor engagement"] = mejor_engagement.get("Engagement", 0)
            analisis["Impresiones mejor engagement"] = mejor_engagement.get("Impresiones", 0)
            analisis["Interacciones mejor engagement"] = mejor_engagement.get("Interacciones", 0)
            analisis["Fecha mejor engagement"] = mejor_engagement.get("Fecha", "N/D")
            analisis["URL mejor engagement"] = mejor_engagement.get("URL", "N/D")

        return analisis

    # ======================================================
    # MÉTRICAS
    # ======================================================
    def metricas(self):
        publicaciones = self.obtener_publicaciones()
        estadisticas = {}

        # --------------------------------------------------
        # PUBLICACIONES INDIVIDUALMENTE DISPONIBLES
        # --------------------------------------------------
        estadisticas["Publicaciones disponibles para análisis"] = len(publicaciones)

        # --------------------------------------------------
        # IMPRESIONES DE LAS PUBLICACIONES DISPONIBLES
        # --------------------------------------------------
        serie_impresiones = pd.Series([
            p["Impresiones"]
            for p in publicaciones
            if p.get("Impresiones") is not None
        ], dtype="float64")

        if not serie_impresiones.empty:
            estadisticas["Impresiones de publicaciones disponibles"] = int(
                serie_impresiones.sum()
            )
            estadisticas["Impresiones medias"] = round(
                serie_impresiones.mean(), 1
            )
            estadisticas["Mediana de impresiones"] = round(
                serie_impresiones.median(), 1
            )
            estadisticas["Mínimo impresiones"] = int(serie_impresiones.min())
            estadisticas["Máximo impresiones"] = int(serie_impresiones.max())
            estadisticas["Desviación estándar impresiones"] = round(
                serie_impresiones.std(), 1
            )
            estadisticas["Publicaciones por encima de la media"] = int(
                (serie_impresiones > serie_impresiones.mean()).sum()
            )
            estadisticas["Publicaciones por debajo de la media"] = int(
                (serie_impresiones < serie_impresiones.mean()).sum()
            )

        # --------------------------------------------------
        # HISTÓRICO COMPLETO
        # --------------------------------------------------
        historico = self.metricas_historicas()
        estadisticas.update(historico)

        # --------------------------------------------------
        # IMPORTANTE: NO CALCULAMOS FRECUENCIA REAL DE PUBLICACIÓN
        # --------------------------------------------------
        estadisticas[
            "Frecuencia real de publicación"
        ] = "No determinable con PUBLICACIONES PRINCIPALES: LinkedIn limita esta lista a 50 registros."

        return estadisticas

    # ======================================================
    # NIVEL DE MADUREZ
    # ======================================================
    def nivel_madurez(self):
        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {
                "actividad": "No determinable",
                "traccion": "Sin datos suficientes",
                "madurez_estrategica": "Inicial"
            }

        publicaciones_validas = [
            p for p in publicaciones
            if p.get("Impresiones") is not None
        ]

        if not publicaciones_validas:
            return {
                "actividad": "No determinable",
                "traccion": "Sin datos suficientes",
                "madurez_estrategica": "Inicial"
            }

        # No usamos el número de publicaciones disponibles para medir
        # experiencia en LinkedIn: el propio exportador limita la muestra.
        actividad = "Muestra de publicaciones disponible"

        analisis = self.analisis_rendimiento()
        porcentaje_sobre_media = analisis.get("Porcentaje sobre la media", 0)
        mayor_alcance = analisis.get("Mayor alcance", 0)

        if mayor_alcance == 0:
            traccion = "Sin datos suficientes"
        elif porcentaje_sobre_media < 20:
            traccion = "Inicial con picos de alcance"
        elif porcentaje_sobre_media < 40:
            traccion = "En desarrollo"
        else:
            traccion = "Consolidada"

        return {
            "actividad": actividad,
            "traccion": traccion,
            "madurez_estrategica": "Inicial"
        }

    # ======================================================
    # RESUMEN PARA IA
    # ======================================================
    def resumen_para_ia(self):

        resumen = self.metricas()
        madurez = self.nivel_madurez()
        periodo = self.obtener_periodo()
        destacadas = self.publicaciones_destacadas()

        texto = []

        # ==================================================
        # CABECERA
        # ==================================================

        texto.append("RESUMEN DEL HISTÓRICO DE LINKEDIN")
        texto.append("")

        # ==================================================
        # MADUREZ DEL PERFIL
        # ==================================================

        texto.append("NIVEL DE MADUREZ DEL PERFIL")

        texto.append(
            f"Actividad: {madurez.get('actividad', 'N/D')}"
        )

        texto.append(
            f"Tracción: {madurez.get('traccion', 'N/D')}"
        )

        texto.append(
            f"Madurez estratégica: "
            f"{madurez.get('madurez_estrategica', 'N/D')}"
        )

        # ==================================================
        # PERIODO
        # ==================================================

        if periodo:

            texto.append("")

            texto.append(
                f"Periodo histórico exportado: "
                f"{periodo[0]} - {periodo[1]}"
            )

        # ==================================================
        # NOTA SOBRE LOS DATOS
        # ==================================================

        texto.append("")

        texto.append("NOTA SOBRE EL ALCANCE DE LOS DATOS")

        texto.append(
            "PUBLICACIONES PRINCIPALES contiene las publicaciones "
            "disponibles en la exportación analizada. El análisis "
            "cuantitativo debe basarse exclusivamente en las métricas "
            "calculadas por Python. No deben inventarse métricas, "
            "publicaciones, causas ni conclusiones que no estén "
            "respaldadas por los datos."
        )

        # ==================================================
        # MÉTRICAS CALCULADAS POR PYTHON
        # ==================================================

        texto.append("")

        texto.append("MÉTRICAS CALCULADAS POR PYTHON")

        texto.append("")

        for clave, valor in resumen.items():

            texto.append(
                f"{clave}: {valor}"
            )

        # ==================================================
        # PUBLICACIONES DESTACADAS
        # ==================================================

        texto.append("")

        texto.append("PUBLICACIONES DESTACADAS")

        texto.append("")

        # --------------------------------------------------
        # TOP 5 IMPRESIONES
        # --------------------------------------------------

        texto.append(
            "TOP 5 PUBLICACIONES POR IMPRESIONES"
        )

        for posicion, publicacion in enumerate(
            destacadas.get("Top 5", []),
            start=1
        ):

            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 'N/D')} | "
                f"Engagement: {publicacion.get('Engagement', 'N/D')}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # --------------------------------------------------
        # BOTTOM 5 IMPRESIONES
        # --------------------------------------------------

        texto.append("")

        texto.append(
            "BOTTOM 5 PUBLICACIONES POR IMPRESIONES"
        )

        for posicion, publicacion in enumerate(
            destacadas.get("Bottom 5", []),
            start=1
        ):

            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 'N/D')} | "
                f"Engagement: {publicacion.get('Engagement', 'N/D')}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # --------------------------------------------------
        # TOP 5 ENGAGEMENT
        # --------------------------------------------------

        texto.append("")

        texto.append(
            "TOP 5 PUBLICACIONES POR ENGAGEMENT"
        )

        for posicion, publicacion in enumerate(
            destacadas.get("Top 5 Engagement", []),
            start=1
        ):

            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 'N/D')} | "
                f"Engagement: {publicacion.get('Engagement', 'N/D')}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # ==================================================
        # DEVOLVER RESUMEN
        # ==================================================

        return "\n".join(texto)

    # ======================================================
    # CONTEXTO ESTRATÉGICO DEL USUARIO
    # ======================================================
    def contexto_estrategico(
        self,
        sector="",
        intereses="",
        objetivo="",
        fecha_activacion=""
    ):
        texto_contexto = []

        texto_contexto.append("CONTEXTO ESTRATÉGICO DECLARADO POR EL USUARIO")
        texto_contexto.append("")

        texto_contexto.append(
            f"Sector objetivo: {sector if sector else 'N/D'}"
        )

        texto_contexto.append(
            f"Intereses profesionales: {intereses if intereses else 'N/D'}"
        )

        texto_contexto.append(
            f"Objetivo profesional: {objetivo if objetivo else 'N/D'}"
        )

        texto_contexto.append(
            f"Fecha de activación estratégica: "
            f"{fecha_activacion if fecha_activacion else 'N/D'}"
        )

        texto_contexto.append("")
        texto_contexto.append("CONTEXTO SOBRE LA EXPERIENCIA EN LINKEDIN")

        texto_contexto.append(
            "El usuario se encuentra todavía en una etapa inicial de uso "
            "de LinkedIn. Lleva pocos meses utilizando la plataforma de "
            "forma activa y se considera principiante en LinkedIn."
        )

        texto_contexto.append(
            "El volumen de publicaciones registrado en los datos no debe "
            "interpretarse como una medida de experiencia, antigüedad o "
            "dominio avanzado de LinkedIn. Las publicaciones representan "
            "actividad realizada durante el periodo analizado."
        )

        texto_contexto.append(
            "La experiencia profesional, académica o técnica previa del "
            "usuario no debe confundirse con su experiencia específica en "
            "LinkedIn."
        )

        texto_contexto.append(
            "El análisis debe valorar los resultados de LinkedIn teniendo "
            "en cuenta la etapa actual del usuario y su contexto profesional, "
            "evitando presentar la actividad realizada en la plataforma como "
            "evidencia de experiencia avanzada en LinkedIn."
        )

        texto_contexto.append("")
        texto_contexto.append("REGLAS DE INTERPRETACIÓN DEL CONTEXTO")

        texto_contexto.append(
            "La actividad, el número de publicaciones y las métricas de "
            "rendimiento deben utilizarse para evaluar comportamiento y "
            "resultados observables, no para determinar por sí solas el "
            "nivel de experiencia del usuario en LinkedIn."
        )

        texto_contexto.append(
            "No debe confundirse actividad con experiencia, volumen de "
            "publicaciones con madurez en LinkedIn, alcance con influencia "
            "ni engagement con impacto profesional."
        )

        texto_contexto.append(
            "Las conclusiones sobre experiencia, madurez o evolución "
            "estratégica deben estar respaldadas por los datos disponibles "
            "y por el contexto declarado, evitando inferencias no demostradas."
        )

        texto_contexto.append("")
        texto_contexto.append("ALCANCE DE LA FECHA DE ACTIVACIÓN")

        texto_contexto.append(
            "La fecha de activación no define el periodo de auditoría. "
            "Solo sirve para contextualizar el tiempo transcurrido desde "
            "la activación declarada y, cuando proceda, interpretar datos "
            "históricos anteriores sin convertirla en fecha de inicio "
            "del análisis."
        )

        return "\n".join(texto_contexto)
