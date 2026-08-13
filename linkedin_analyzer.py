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

    # ======================================================
    # INICIALIZACIÓN
    # ======================================================
    def __init__(
        self,
        dataframe,
        interaccion_dataframe=None,
        fecha_corte=None
    ):
        self.df_original = dataframe.copy()
        self.df = self._limpiar_dataframe()

        self.df_interaccion_original = (
            interaccion_dataframe.copy()
            if interaccion_dataframe is not None
            else pd.DataFrame()
        )
        self.df_interaccion = self._limpiar_interaccion()

        # --------------------------------------------------
        # FECHA DE CORTE DE LA AUDITORÍA
        # --------------------------------------------------
        # Se utiliza para calcular la antigüedad de cada
        # publicación en el momento de la auditoría.
        #
        # Si la aplicación no proporciona una fecha concreta,
        # se utiliza la fecha actual del sistema.
        # --------------------------------------------------

        if fecha_corte is None:
            self.fecha_corte = pd.Timestamp.today().normalize()
        else:
            self.fecha_corte = pd.to_datetime(
                fecha_corte,
                errors="coerce"
            )

            if pd.isna(self.fecha_corte):
                self.fecha_corte = pd.Timestamp.today().normalize()
            else:
                self.fecha_corte = self.fecha_corte.normalize()

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

        # ==================================================
        # EDAD TEMPORAL DE LAS PUBLICACIONES
        #
        # La edad se calcula respecto al FINAL DEL HISTÓRICO
        # exportado por LinkedIn, no respecto a la fecha actual.
        #
        # Esto permite comparar correctamente publicaciones
        # que han tenido diferentes ventanas de distribución.
        # ==================================================

        periodo = self.obtener_periodo()

        fecha_referencia = None

        if periodo:
            fecha_referencia = pd.to_datetime(
                periodo[1],
                dayfirst=True,
                errors="coerce"
            )

        for publicacion in publicaciones:

            fecha_texto = publicacion.get("Fecha")

            if (
                fecha_referencia is not None
                and pd.notna(fecha_referencia)
                and fecha_texto
            ):

                fecha_publicacion = pd.to_datetime(
                    fecha_texto,
                    dayfirst=True,
                    errors="coerce"
                )

                if pd.notna(fecha_publicacion):

                    edad = max(
                        0,
                        (fecha_referencia - fecha_publicacion).days
                    )

                    publicacion["Edad (días)"] = int(edad)

                    # ------------------------------------------
                    # CLASIFICACIÓN TEMPORAL
                    # ------------------------------------------

                    if edad <= 2:

                        publicacion["Madurez temporal"] = "Muy reciente"

                        publicacion["Nivel de observación"] = (
                            "Insuficiente para evaluar rendimiento acumulado"
                        )

                    elif edad <= 6:

                        publicacion["Madurez temporal"] = "Reciente"

                        publicacion["Nivel de observación"] = (
                            "Observación temprana"
                        )

                    elif edad < 14:

                        publicacion["Madurez temporal"] = "En observación"

                        publicacion["Nivel de observación"] = (
                            "Observación todavía limitada"
                        )

                    elif edad < 30:

                        publicacion["Madurez temporal"] = "Madura"

                        publicacion["Nivel de observación"] = (
                            "Observación suficiente para comparación acumulada"
                        )

                    else:

                        publicacion["Madurez temporal"] = "Muy madura"

                        publicacion["Nivel de observación"] = (
                            "Observación amplia"
                        )

        # ==================================================
        # ENGAGEMENT
        # ==================================================

        for publicacion in publicaciones:

            impresiones = publicacion.get("Impresiones")
            interacciones = publicacion.get("Interacciones")

            if (
                impresiones is not None
                and impresiones > 0
                and interacciones is not None
            ):

                publicacion["Engagement"] = round(
                    (interacciones / impresiones) * 100,
                    2
                )



        # ==================================================
        # ENRIQUECIMIENTO ANALÍTICO DE LAS PUBLICACIONES
        # ==================================================

        for publicacion in publicaciones:

            # ----------------------------------------------
            # ENGAGEMENT
            # ----------------------------------------------

            impresiones = publicacion.get("Impresiones")
            interacciones = publicacion.get("Interacciones")

            if (
                impresiones is not None
                and impresiones > 0
                and interacciones is not None
            ):
                publicacion["Engagement"] = round(
                    (interacciones / impresiones) * 100,
                    2
                )

            # ----------------------------------------------
            # MADUREZ TEMPORAL
            # ----------------------------------------------

            fecha = publicacion.get("Fecha")

            madurez = self.calcular_madurez_publicacion(
                fecha
            )

            publicacion["Edad (días)"] = madurez[
                "Edad (días)"
            ]

            publicacion["Madurez"] = madurez[
                "Madurez"
            ]

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
    # MADUREZ TEMPORAL DE LAS PUBLICACIONES
    # ======================================================
    def calcular_madurez_publicacion(self, fecha_publicacion):
        """
        Determina la antigüedad de una publicación respecto
        a la fecha de corte de la auditoría.

        La antigüedad NO se utiliza para estimar una velocidad
        lineal de distribución de LinkedIn.

        Su función es evitar comparar directamente publicaciones
        recién publicadas con publicaciones que llevan mucho
        tiempo disponibles.
        """

        fecha = pd.to_datetime(
            fecha_publicacion,
            errors="coerce",
            dayfirst=True
        )

        if pd.isna(fecha):
            return {
                "Edad (días)": None,
                "Madurez": "NO DETERMINABLE"
            }

        fecha = fecha.normalize()

        edad = max(
            0,
            int((self.fecha_corte - fecha).days)
        )

        # --------------------------------------------------
        # CLASIFICACIÓN TEMPORAL
        # --------------------------------------------------

        if edad <= 2:

            madurez = "MUY RECIENTE"

        elif edad <= 6:

            madurez = "RECIENTE"

        elif edad <= 13:

            madurez = "EN CONSOLIDACIÓN"

        elif edad <= 29:

            madurez = "MADURA"

        else:

            madurez = "HISTÓRICA"

        return {
            "Edad (días)": edad,
            "Madurez": madurez
        }

    # ======================================================
    # PUBLICACIONES DESTACADAS
    # ======================================================

    def publicaciones_destacadas(self):

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {
                "Top 5": [],
                "Bottom 5": [],
                "Top 5 Engagement": [],
                "Top 5 Engagement Maduras": [],
                "Recientes en Observación": [],
                "Bajo Rendimiento Maduro": []
            }

        # ==================================================
        # PUBLICACIONES CON IMPRESIONES
        # ==================================================

        publicaciones_con_impresiones = [
            p
            for p in publicaciones
            if p.get("Impresiones") is not None
        ]

        # ==================================================
        # TOP 5 ALCANCE ACUMULADO
        # ==================================================

        top_5 = sorted(
            publicaciones_con_impresiones,
            key=lambda p: p.get("Impresiones", 0),
            reverse=True
        )[:5]

        # ==================================================
        # BOTTOM 5 ALCANCE ACUMULADO
        #
        # IMPORTANTE:
        # Este ranking se conserva como dato descriptivo,
        # pero NO debe interpretarse automáticamente como
        # "peores publicaciones".
        # ==================================================

        bottom_5 = sorted(
            publicaciones_con_impresiones,
            key=lambda p: p.get("Impresiones", 0)
        )[:5]

        # ==================================================
        # TOP 5 ENGAGEMENT GENERAL
        # ==================================================

        publicaciones_con_engagement = [
            p
            for p in publicaciones
            if p.get("Engagement") is not None
        ]

        top_engagement = sorted(
            publicaciones_con_engagement,
            key=lambda p: p.get("Engagement", 0),
            reverse=True
        )[:5]

        # ==================================================
        # PUBLICACIONES MADURAS
        #
        # Para comparar rendimiento acumulado evitamos
        # publicaciones demasiado recientes.
        # ==================================================

        publicaciones_maduras = [
            p
            for p in publicaciones_con_engagement
            if p.get("Edad (días)") is not None
            and p.get("Edad (días)") >= 14
        ]

        # ==================================================
        # TOP 5 ENGAGEMENT ENTRE PUBLICACIONES MADURAS
        # ==================================================

        top_engagement_maduras = sorted(
            publicaciones_maduras,
            key=lambda p: p.get("Engagement", 0),
            reverse=True
        )[:5]

        # ==================================================
        # PUBLICACIONES RECIENTES EN OBSERVACIÓN
        # ==================================================

        recientes_observacion = [
            p
            for p in publicaciones
            if p.get("Edad (días)") is not None
            and p.get("Edad (días)") <= 6
        ]

        recientes_observacion = sorted(
            recientes_observacion,
            key=lambda p: p.get("Edad (días)", 999)
        )

        # ==================================================
        # PUBLICACIONES MADURAS CON MENOR ALCANCE
        #
        # Este ranking sí es mucho más útil que un Bottom 5
        # absoluto para detectar publicaciones que han tenido
        # suficiente tiempo para acumular distribución.
        # ==================================================

        bajo_rendimiento_maduro = [
            p
            for p in publicaciones_con_impresiones
            if p.get("Edad (días)") is not None
            and p.get("Edad (días)") >= 14
        ]

        bajo_rendimiento_maduro = sorted(
            bajo_rendimiento_maduro,
            key=lambda p: p.get("Impresiones", 0)
        )[:5]

        return {
            "Top 5": top_5,
            "Bottom 5": bottom_5,
            "Top 5 Engagement": top_engagement,
            "Top 5 Engagement Maduras": top_engagement_maduras,
            "Recientes en Observación": recientes_observacion,
            "Bajo Rendimiento Maduro": bajo_rendimiento_maduro
        }

    # ======================================================
    # MADUREZ TEMPORAL DE LAS PUBLICACIONES
    # ======================================================
    def analizar_antiguedad_publicaciones(self):
        """
        Analiza cuánto tiempo lleva disponible cada publicación
        dentro del periodo histórico exportado.

        IMPORTANTE:
        - No considera automáticamente una publicación reciente como
          fracaso por tener pocas impresiones.
        - No convierte impresiones/día en una métrica de calidad.
        - Permite distinguir rendimiento acumulado de tiempo de exposición.
        - La fecha de referencia es el FINAL DEL HISTÓRICO EXPORTADO,
          no la fecha actual del sistema.
        """

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return []

        periodo = self.obtener_periodo()

        if not periodo:
            return []

        try:
            fecha_referencia = pd.to_datetime(
                periodo[1],
                dayfirst=True,
                errors="coerce"
            )
        except Exception:
            return []

        if pd.isna(fecha_referencia):
            return []

        resultado = []

        for publicacion in publicaciones:

            fecha_texto = publicacion.get("Fecha")

            if not fecha_texto:
                continue

            fecha_publicacion = pd.to_datetime(
                fecha_texto,
                dayfirst=True,
                errors="coerce"
            )

            if pd.isna(fecha_publicacion):
                continue

            dias_desde_publicacion = max(
                0,
                (fecha_referencia - fecha_publicacion).days
            )

            publicacion_analizada = publicacion.copy()

            publicacion_analizada[
                "Días desde publicación"
            ] = int(dias_desde_publicacion)

            # --------------------------------------------------
            # CLASIFICACIÓN DE MADUREZ
            # --------------------------------------------------

            if dias_desde_publicacion <= 2:

                madurez = "Muy reciente"

            elif dias_desde_publicacion <= 7:

                madurez = "Reciente"

            elif dias_desde_publicacion <= 30:

                madurez = "Maduración"

            else:

                madurez = "Madura"

            publicacion_analizada[
                "Madurez temporal"
            ] = madurez

            # --------------------------------------------------
            # NIVEL DE OBSERVACIÓN
            # --------------------------------------------------

            if dias_desde_publicacion <= 2:

                observacion = (
                    "Insuficiente para evaluar rendimiento acumulado"
                )

            elif dias_desde_publicacion <= 7:

                observacion = (
                    "Observación temprana"
                )

            else:

                observacion = (
                    "Observación suficiente para comparación acumulada"
                )

            publicacion_analizada[
                "Nivel de observación"
            ] = observacion

            # --------------------------------------------------
            # VELOCIDAD DE DISTRIBUCIÓN
            # --------------------------------------------------
            # Se calcula SOLO como indicador auxiliar.
            # Nunca debe interpretarse automáticamente como
            # calidad o éxito de la publicación.

            impresiones = publicacion.get("Impresiones")

            if impresiones is not None:

                dias_observacion = max(
                    1,
                    dias_desde_publicacion + 1
                )

                publicacion_analizada[
                    "Impresiones por día de observación"
                ] = round(
                    impresiones / dias_observacion,
                    2
                )

            resultado.append(publicacion_analizada)

        return resultado

    # ======================================================
    # PUBLICACIONES COMPARABLES TEMPORALMENTE
    # ======================================================
    def publicaciones_comparables(self, dias_minimos=7):
        """
        Devuelve únicamente publicaciones que han tenido al menos
        'dias_minimos' de exposición.

        Sirve para evitar que las publicaciones recién publicadas
        sean clasificadas prematuramente como éxitos o fracasos.
        """

        publicaciones = self.analizar_antiguedad_publicaciones()

        if not publicaciones:
            return []

        return [
            p for p in publicaciones
            if p.get("Días desde publicación", 0) >= dias_minimos
        ]

    # ======================================================
    # PUBLICACIONES DEMASIADO RECIENTES PARA EVALUAR
    # ======================================================
    def publicaciones_recientes(self, dias_maximos=6):
        """
        Identifica publicaciones que todavía no deberían utilizarse
        como evidencia de bajo rendimiento acumulado.
        """

        publicaciones = self.analizar_antiguedad_publicaciones()

        if not publicaciones:
            return []

        return [
            p for p in publicaciones
            if p.get("Días desde publicación", 0) <= dias_maximos
        ]

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

        texto.append("RESUMEN ANALÍTICO DEL HISTÓRICO DE LINKEDIN")
        texto.append("")
        texto.append(
            "Este bloque constituye la fuente estructurada de datos que "
            "recibirá la IA para elaborar la auditoría estratégica."
        )

        # ==================================================
        # REGLA FUNDAMENTAL DE INTERPRETACIÓN
        # ==================================================

        texto.append("")
        texto.append("REGLA FUNDAMENTAL DE INTERPRETACIÓN")

        texto.append(
            "Los valores numéricos calculados por Python son la fuente de "
            "verdad del análisis cuantitativo. La IA no debe modificar, "
            "recalcular, sustituir ni inventar cifras."
        )

        texto.append(
            "La IA puede interpretar los datos y formular hipótesis "
            "estratégicas, pero debe distinguir siempre entre HECHO, "
            "INFERENCIA e HIPÓTESIS."
        )

        texto.append(
            "Ninguna relación causal debe afirmarse como hecho si los datos "
            "disponibles únicamente permiten establecer una correlación, "
            "coincidencia o posible explicación."
        )

        # ==================================================
        # MADUREZ DEL PERFIL
        # ==================================================

        texto.append("")
        texto.append("NIVEL DE MADUREZ CALCULADO POR EL SISTEMA")

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

        texto.append("")
        texto.append(
            "IMPORTANTE: estos niveles son indicadores analíticos calculados "
            "por el sistema a partir de los datos disponibles. No deben "
            "interpretarse automáticamente como una medida de experiencia "
            "profesional, experiencia laboral, antigüedad en LinkedIn o "
            "competencia del usuario."
        )

        # ==================================================
        # PERIODO DEL HISTÓRICO
        # ==================================================

        if periodo:

            texto.append("")
            texto.append("PERIODO DEL HISTÓRICO EXPORTADO")

            texto.append(
                f"Desde: {periodo[0]}"
            )

            texto.append(
                f"Hasta: {periodo[1]}"
            )

        # ==================================================
        # ALCANCE Y NATURALEZA DE LAS FUENTES
        # ==================================================

        texto.append("")
        texto.append("ALCANCE Y NATURALEZA DE LOS DATOS")

        texto.append(
            "El archivo exportado de LinkedIn contiene diferentes fuentes "
            "de información que no deben mezclarse automáticamente."
        )

        texto.append("")
        texto.append(
            "1. HISTÓRICO DIARIO DE INTERACCIÓN"
        )

        texto.append(
            "El histórico diario representa los datos disponibles para cada "
            "día del periodo exportado. Cuando Python utiliza estos datos "
            "para calcular impresiones, interacciones u otras métricas "
            "acumuladas del periodo, dichas métricas deben considerarse "
            "representativas del histórico exportado."
        )

        texto.append("")
        texto.append(
            "2. PUBLICACIONES PRINCIPALES"
        )

        texto.append(
            "La lista de publicaciones principales contiene únicamente las "
            "publicaciones disponibles en la exportación analizada. LinkedIn "
            "puede limitar esta relación y presentar rankings independientes "
            "por distintas métricas."
        )

        texto.append(
            "Por tanto, el número de publicaciones disponibles para análisis "
            "NO debe interpretarse automáticamente como el número total de "
            "publicaciones realizadas durante el periodo."
        )

        texto.append(
            "Tampoco debe utilizarse esta lista para calcular o afirmar la "
            "frecuencia real de publicación del usuario."
        )

        # ==================================================
        # REGLAS PARA LA FRECUENCIA
        # ==================================================

        texto.append("")
        texto.append("REGLAS SOBRE FRECUENCIA Y ACTIVIDAD")

        texto.append(
            "No debe inferirse la frecuencia real de publicación a partir "
            "del número de registros presentes en PUBLICACIONES PRINCIPALES."
        )

        texto.append(
            "Si Python proporciona métricas de frecuencia calculadas a partir "
            "de una fuente temporal válida, la IA puede utilizarlas."
        )

        texto.append(
            "Si no existe una métrica de frecuencia calculada por Python, "
            "la IA debe indicar que la frecuencia exacta no puede determinarse "
            "con los datos disponibles."
        )

        texto.append(
            "Nunca debe utilizarse la expresión 'publica frecuentemente', "
            "'publica poco', 'actividad intermitente' o similares únicamente "
            "porque existan pocos o muchos registros en PUBLICACIONES PRINCIPALES."
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
        # REGLAS PARA LAS MÉTRICAS
        # ==================================================

        texto.append("")
        texto.append("REGLAS PARA INTERPRETAR LAS MÉTRICAS")

        texto.append(
            "Las métricas anteriores son las cifras oficiales que deben "
            "utilizarse en el informe."
        )

        texto.append(
            "Si una métrica no aparece en este bloque, la IA no debe inventarla "
            "ni estimarla salvo que pueda derivarse directamente de otra cifra "
            "proporcionada y dicha derivación sea matemáticamente inequívoca."
        )

        texto.append(
            "Las métricas procedentes de fuentes diferentes deben mantenerse "
            "separadas y no deben sumarse, compararse o relacionarse sin "
            "justificación metodológica."
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
            "TOP 5 PUBLICACIONES DISPONIBLES POR IMPRESIONES"
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
            "BOTTOM 5 PUBLICACIONES DISPONIBLES POR IMPRESIONES"
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
            "TOP 5 PUBLICACIONES DISPONIBLES POR ENGAGEMENT"
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
        # LIMITACIONES METODOLÓGICAS
        # ==================================================

        texto.append("")
        texto.append("LIMITACIONES METODOLÓGICAS")

        texto.append(
            "La auditoría debe reconocer explícitamente cualquier limitación "
            "derivada de la estructura de la exportación de LinkedIn."
        )

        texto.append(
            "La ausencia de determinados registros no demuestra que una "
            "actividad no haya ocurrido."
        )

        texto.append(
            "La presencia de una publicación en un ranking no demuestra por "
            "sí sola que sus características sean la causa de su rendimiento."
        )

        texto.append(
            "Las publicaciones destacadas deben utilizarse como evidencia "
            "para identificar patrones y formular hipótesis, no como prueba "
            "causal."
        )

        # ==================================================
        # CRITERIO FINAL PARA LA IA
        # ==================================================

        texto.append("")
        texto.append("CRITERIO FINAL")

        texto.append(
            "La auditoría debe priorizar precisión metodológica sobre "
            "apariencia de certeza. Cuando los datos permitan una conclusión, "
            "debe expresarse con claridad. Cuando solo permitan una hipótesis, "
            "debe presentarse como hipótesis. Cuando no permitan responder, "
            "debe indicarse expresamente que el dato no puede determinarse."
        )

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
