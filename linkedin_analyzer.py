import pandas as pd
import numpy as np


class LinkedInAnalyzer:

    def __init__(self, dataframe):
        self.df_original = dataframe.copy()
        self.df = self._limpiar_dataframe()

    # ======================================================
    # DETECTAR AUTOMÁTICAMENTE FECHAS
    # ======================================================
    def obtener_periodo(self):

        posibles = [
            # Español
            "Fecha",
            "Fecha de publicación",
            "Fecha de creación",
            "Fecha de publicación del contenido",

            # Inglés
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
    # LIMPIEZA
    # ======================================================

    def _limpiar_dataframe(self):

        df = self.df_original.copy()

        # Eliminar columnas totalmente vacías
        df = df.dropna(axis=1, how="all")

        # Eliminar columnas completamente a cero
        columnas_validas = []

        for col in df.columns:

            serie = pd.to_numeric(df[col], errors="coerce")

            # Si es texto la dejamos
            if serie.isna().all():
                columnas_validas.append(col)
                continue

            # Si tiene algún dato distinto de 0
            if not (serie.fillna(0) == 0).all():
                columnas_validas.append(col)

        df = df[columnas_validas]

        # Quitar espacios en nombres
        df.columns = df.columns.str.strip()

        return df

    # ======================================================
    # BUSCAR COLUMNAS
    # ======================================================

    def buscar_columna(self, posibles):

        for nombre in posibles:
            if nombre in self.df.columns:
                return nombre

        return None

    # ======================================================
    # NORMALIZAR PUBLICACIONES PRINCIPALES
    # ======================================================

    def obtener_publicaciones(self):

        url_columna = self.buscar_columna([
            "URL de la publicación",
            "URL"
        ])

        fecha_columna = self.buscar_columna([
            "Fecha de publicación",
            "Fecha"
        ])

        interacciones_columna = self.buscar_columna([
            "Interacciones"
        ])

        impresiones_columna = self.buscar_columna([
            "Impresiones",
            "Impressions"
        ])

        if url_columna is None:
            return []

        publicaciones = []

        for _, fila in self.df.iterrows():

            url = fila[url_columna]

            # Ignorar filas sin URL
            if pd.isna(url) or str(url).strip() == "":
                continue

            publicacion = {
                "URL": str(url).strip()
            }

            # ----------------------------------------------
            # FECHA
            # ----------------------------------------------

            if fecha_columna:

                fecha = pd.to_datetime(
                    fila[fecha_columna],
                    errors="coerce",
                    dayfirst=True
                )

                if pd.notna(fecha):
                    publicacion["Fecha"] = fecha.strftime(
                        "%d/%m/%Y"
                    )

            # ----------------------------------------------
            # INTERACCIONES
            # ----------------------------------------------

            if interacciones_columna:

                interacciones = pd.to_numeric(
                    fila[interacciones_columna],
                    errors="coerce"
                )

                if pd.notna(interacciones):
                    publicacion["Interacciones"] = int(
                        interacciones
                    )

            # ----------------------------------------------
            # IMPRESIONES
            # ----------------------------------------------

            if impresiones_columna:

                impresiones = pd.to_numeric(
                    fila[impresiones_columna],
                    errors="coerce"
                )

                if pd.notna(impresiones):
                    publicacion["Impresiones"] = int(
                        impresiones
                    )

            publicaciones.append(publicacion)

        return publicaciones

    # ======================================================
    # PUBLICACIONES DESTACADAS
    # ======================================================

    def publicaciones_destacadas(self):

        publicaciones = self.obtener_publicaciones()

        # Asegurar que todas las publicaciones tienen Engagement
        for publicacion in publicaciones:

            impresiones = publicacion.get("Impresiones", 0)
            interacciones = publicacion.get("Interacciones", 0)

            if impresiones > 0:

                publicacion["Engagement"] = round(
                    (interacciones / impresiones) * 100,
                    2
                )

            else:

                publicacion["Engagement"] = 0.0

          

        if not publicaciones:
            return {
                "Top 5": [],
                "Bottom 5": []
            }

        publicaciones_validas = [
            p for p in publicaciones
            if "Impresiones" in p
        ]

        # --------------------------------------------------
        # TOP 5
        # --------------------------------------------------

        top_5 = sorted(
            publicaciones_validas,
            key=lambda p: p["Impresiones"],
            reverse=True
        )[:5]

        # --------------------------------------------------
        # BOTTOM 5
        # --------------------------------------------------

        bottom_5 = sorted(
            publicaciones_validas,
            key=lambda p: p["Impresiones"]
        )[:5]

        # --------------------------------------------------
        # TOP 5 POR ENGAGEMENT
        # --------------------------------------------------

        top_engagement = sorted(
            publicaciones_validas,
            key=lambda p: p.get("Engagement", 0),
            reverse=True
        )[:5]

        return {
            "Top 5": top_5,
            "Bottom 5": bottom_5,
            "Top 5 Engagement": top_engagement
        }

    # ======================================================
    # ANÁLISIS DE RENDIMIENTO
    # ======================================================

    def analisis_rendimiento(self):

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {}

        publicaciones_validas = [
            p for p in publicaciones
            if p.get("Impresiones", 0) > 0
        ]

        if not publicaciones_validas:
            return {}

        analisis = {}

        # --------------------------------------------------
        # IMPRESIONES
        # --------------------------------------------------

        impresiones = [
            p["Impresiones"]
            for p in publicaciones_validas
        ]

        media_impresiones = sum(impresiones) / len(impresiones)

        # --------------------------------------------------
        # MEDIANA DE IMPRESIONES
        # --------------------------------------------------

        impresiones_ordenadas = sorted(impresiones)

        n = len(impresiones_ordenadas)

        if n % 2 == 1:

            mediana_impresiones = impresiones_ordenadas[n // 2]

        else:

            mediana_impresiones = (
                impresiones_ordenadas[n // 2 - 1]
                + impresiones_ordenadas[n // 2]
            ) / 2

        analisis["Mediana de impresiones"] = round(
            mediana_impresiones,
            1
        )


        # --------------------------------------------------
        # PUBLICACIONES POR ENCIMA DE LA MEDIA
        # --------------------------------------------------

        publicaciones_sobre_media = [
            p for p in publicaciones_validas
            if p["Impresiones"] > media_impresiones
        ]

        analisis["Publicaciones sobre la media"] = len(
            publicaciones_sobre_media
        )

        analisis["Porcentaje sobre la media"] = round(
            (
                len(publicaciones_sobre_media)
                / len(publicaciones_validas)
            ) * 100,
            1
        )

        # --------------------------------------------------
        # PUBLICACIONES POR DEBAJO DE LA MEDIA
        # --------------------------------------------------

        publicaciones_bajo_media = [
            p for p in publicaciones_validas
            if p["Impresiones"] < media_impresiones
        ]

        analisis["Publicaciones bajo la media"] = len(
            publicaciones_bajo_media
        )

        analisis["Porcentaje bajo la media"] = round(
            (
                len(publicaciones_bajo_media)
                / len(publicaciones_validas)
            ) * 100,
            1
        )


        # --------------------------------------------------
        # MEJOR ENGAGEMENT
        # --------------------------------------------------

        mejor_engagement = None
        mejor_valor_engagement = 0.0

        for publicacion in publicaciones_validas:

            impresiones = publicacion.get("Impresiones", 0)
            interacciones = publicacion.get("Interacciones", 0)

            if impresiones > 0:

                engagement = round(
                    (interacciones / impresiones) * 100,
                    2
                )

                if engagement > mejor_valor_engagement:

                    mejor_valor_engagement = engagement
                    mejor_engagement = publicacion

        if mejor_engagement:

            analisis["Mejor engagement"] = (
                mejor_valor_engagement
            )

            analisis["Impresiones mejor engagement"] = (
                mejor_engagement.get("Impresiones", 0)
            )

            analisis["Interacciones mejor engagement"] = (
                mejor_engagement.get("Interacciones", 0)
            )

            analisis["Fecha mejor engagement"] = (
                mejor_engagement.get("Fecha", "N/D")
            )

            analisis["URL mejor engagement"] = (
                mejor_engagement.get("URL", "N/D")
            )

        # --------------------------------------------------
        # PUBLICACIÓN CON MAYOR ALCANCE
        # --------------------------------------------------

        mejor_alcance = max(
            publicaciones_validas,
            key=lambda p: p["Impresiones"]
        )

        analisis["Mayor alcance"] = (
            mejor_alcance["Impresiones"]
        )

        analisis["Interacciones mayor alcance"] = (
            mejor_alcance.get("Interacciones", 0)
        )

        impresiones_mejor = mejor_alcance.get("Impresiones", 0)
        interacciones_mejor = mejor_alcance.get("Interacciones", 0)

        if impresiones_mejor > 0:

            analisis["Engagement mayor alcance"] = round(
                (interacciones_mejor / impresiones_mejor) * 100,
                2
            )

        else:

            analisis["Engagement mayor alcance"] = 0.0

        analisis["Fecha mayor alcance"] = (
            mejor_alcance.get("Fecha", "N/D")
        )

        # --------------------------------------------------
        # DIFERENCIA ENTRE MEDIA Y MEDIANA
        # --------------------------------------------------

        analisis["Diferencia media-mediana"] = round(
            media_impresiones - mediana_impresiones,
            1
        )

        if mediana_impresiones > 0:

            analisis["Ratio media/mediana"] = round(
                media_impresiones / mediana_impresiones,
                2
            )

        else:

            analisis["Ratio media/mediana"] = 0

        return analisis

    # ======================================================
    # MÉTRICAS
    # ======================================================

    def metricas(self):

        impresiones = self.buscar_columna([
            "Impresiones",
            "Impressions"
        ])

        reacciones = self.buscar_columna([
            "Reacciones",
            "Reactions"
        ])

        comentarios = self.buscar_columna([
            "Comentarios",
            "Comments"
        ])

        compartidos = self.buscar_columna([
            "Compartidos",
            "Shares"
        ])

        estadisticas = {}

        # --------------------------------------------------
        # PUBLICACIONES
        # --------------------------------------------------

        estadisticas["Publicaciones"] = len(self.df)

        # --------------------------------------------------
        # IMPRESIONES
        # --------------------------------------------------

        if impresiones:

            serie_impresiones = pd.to_numeric(
                self.df[impresiones],
                errors="coerce"
            ).dropna()

            if not serie_impresiones.empty:

                estadisticas["Impresiones totales"] = int(
                    serie_impresiones.sum()
                )

                estadisticas["Impresiones medias"] = round(
                    serie_impresiones.mean(),
                    1
                )

                estadisticas["Mediana de impresiones"] = round(
                    serie_impresiones.median(),
                    1
                )

                estadisticas["Mínimo impresiones"] = int(
                    serie_impresiones.min()
                )

                estadisticas["Máximo impresiones"] = int(
                    serie_impresiones.max()
                )

                estadisticas["Desviación estándar impresiones"] = round(
                    serie_impresiones.std(),
                    1
                )

                estadisticas["Publicaciones por encima de la media"] = int(
                    (serie_impresiones > serie_impresiones.mean()).sum()
                )

                estadisticas["Publicaciones por debajo de la media"] = int(
                    (serie_impresiones < serie_impresiones.mean()).sum()
                )

        # --------------------------------------------------
        # FRECUENCIA DE PUBLICACIÓN
        # --------------------------------------------------

        posibles_fechas = [
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

        columna_fecha = self.buscar_columna(posibles_fechas)

        if columna_fecha:

            fechas = pd.to_datetime(
                self.df[columna_fecha],
                errors="coerce",
                dayfirst=True
            ).dropna().sort_values()

            if not fechas.empty:

                fecha_inicio = fechas.min()
                fecha_fin = fechas.max()

                dias_periodo = (
                    fecha_fin - fecha_inicio
                ).days

                # Evitamos divisiones por cero si todas
                # las publicaciones tienen la misma fecha.
                dias_calculo = max(1, dias_periodo)

                semanas_periodo = max(
                    1,
                    dias_calculo / 7
                )

                meses_periodo = max(
                    1,
                    dias_calculo / 30.44
                )

                estadisticas["Días del periodo analizado"] = int(
                    dias_periodo
                )

                estadisticas["Semanas del periodo analizado"] = round(
                    semanas_periodo,
                    1
                )

                estadisticas["Meses del periodo analizado"] = round(
                    meses_periodo,
                    1
                )

                estadisticas["Publicaciones por semana"] = round(
                    len(fechas) / semanas_periodo,
                    2
                )

                estadisticas["Publicaciones por mes"] = round(
                    len(fechas) / meses_periodo,
                    2
                )

                # --------------------------------------------------
                # INTERVALO MEDIO ENTRE PUBLICACIONES
                # --------------------------------------------------

                if len(fechas) > 1:

                    diferencias = fechas.diff().dropna()

                    intervalo_medio = (
                        diferencias.dt.total_seconds().mean()
                        / 86400
                    )

                    estadisticas[
                        "Intervalo medio entre publicaciones (días)"
                    ] = round(
                        intervalo_medio,
                        2
                    )

        # --------------------------------------------------
        # REACCIONES
        # --------------------------------------------------

        if reacciones:

            serie = pd.to_numeric(
                self.df[reacciones],
                errors="coerce"
            ).fillna(0)

            estadisticas["Reacciones totales"] = int(
                serie.sum()
            )

            # --------------------------------------------------
            # ENGAGEMENT GLOBAL
            # --------------------------------------------------

            if impresiones and reacciones:

                serie_impresiones = pd.to_numeric(
                    self.df[impresiones],
                    errors="coerce"
                ).fillna(0)

                serie_reacciones = pd.to_numeric(
                    self.df[reacciones],
                    errors="coerce"
                ).fillna(0)

                impresiones_totales = serie_impresiones.sum()
                reacciones_totales = serie_reacciones.sum()

                if impresiones_totales > 0:

                    engagement_global = (
                        reacciones_totales
                        / impresiones_totales
                    ) * 100

                    estadisticas["Engagement global (%)"] = round(
                        engagement_global,
                        2
                    )

        # --------------------------------------------------
        # COMENTARIOS
        # --------------------------------------------------

        if comentarios:

            serie = pd.to_numeric(
                self.df[comentarios],
                errors="coerce"
            ).fillna(0)

            estadisticas["Comentarios totales"] = int(
                serie.sum()
            )

        # --------------------------------------------------
        # COMPARTIDOS
        # --------------------------------------------------

        if compartidos:

            serie = pd.to_numeric(
                self.df[compartidos],
                errors="coerce"
            ).fillna(0)

            estadisticas["Compartidos totales"] = int(
                serie.sum()
            )

        return estadisticas    
    
    # ======================================================
    # NIVEL DE MADUREZ DEL PERFIL
    # ======================================================

    def nivel_madurez(self):

        publicaciones = self.obtener_publicaciones()

        if not publicaciones:
            return {
                "actividad": "Inicial",
                "traccion": "Sin datos suficientes",
                "madurez_estrategica": "Inicial"
            }

        numero_publicaciones = len(publicaciones)

        publicaciones_validas = [
            p for p in publicaciones
            if p.get("Impresiones", 0) > 0
        ]

        if not publicaciones_validas:
            return {
                "actividad": "Inicial",
                "traccion": "Sin datos suficientes",
                "madurez_estrategica": "Inicial"
            }

        # --------------------------------------------------
        # ACTIVIDAD
        # --------------------------------------------------

        if numero_publicaciones < 15:
            actividad = "Inicial"

        elif numero_publicaciones < 50:
            actividad = "En desarrollo"

        else:
            actividad = "Consolidada"

        # --------------------------------------------------
        # TRACCIÓN
        # --------------------------------------------------

        analisis = self.analisis_rendimiento()

        mayor_alcance = analisis.get(
            "Mayor alcance",
            0
        )

        publicaciones_sobre_media = analisis.get(
            "Publicaciones sobre la media",
            0
        )

        porcentaje_sobre_media = analisis.get(
            "Porcentaje sobre la media",
            0
        )

        if mayor_alcance == 0:
            traccion = "Sin datos suficientes"

        elif porcentaje_sobre_media < 20:
            traccion = "Inicial con picos de alcance"

        elif porcentaje_sobre_media < 40:
            traccion = "En desarrollo"

        else:
            traccion = "Consolidada"

        # --------------------------------------------------
        # MADUREZ ESTRATÉGICA
        # --------------------------------------------------

        # Importante:
        # No confundimos cantidad de publicaciones
        # con experiencia estratégica en LinkedIn.

        if numero_publicaciones < 15:

            madurez_estrategica = "Inicial"

        elif numero_publicaciones < 50:

            madurez_estrategica = "Inicial"

        else:

            madurez_estrategica = "En desarrollo"

        return {
            "actividad": actividad,
            "traccion": traccion,
            "madurez_estrategica": madurez_estrategica
        }

    # ======================================================
    # RESUMEN PARA IA
    # ======================================================

    def resumen_para_ia(self):
        resumen = self.metricas()
        madurez = self.nivel_madurez()
        texto = []

        texto.append("RESUMEN DEL HISTÓRICO DE LINKEDIN")

        # --------------------------------------------------
        # NIVEL DE MADUREZ DEL PERFIL
        # --------------------------------------------------
        texto.append("")
        texto.append("NIVEL DE MADUREZ DEL PERFIL")
        texto.append(f"Actividad: {madurez.get('actividad', 'N/D')}")
        texto.append(f"Tracción: {madurez.get('traccion', 'N/D')}")
        texto.append(f"Madurez estratégica: {madurez.get('madurez_estrategica', 'N/D')}")

        # --------------------------------------------------
        # PERIODO
        # --------------------------------------------------
        periodo = self.obtener_periodo()
        if periodo:
            texto.append("")
            texto.append(f"Periodo analizado: {periodo[0]} - {periodo[1]}")

        # --------------------------------------------------
        # MÉTRICAS GENERALES
        # --------------------------------------------------
        texto.append("")
        for clave, valor in resumen.items():
            texto.append(f"{clave}: {valor}")

        # --------------------------------------------------
        # PUBLICACIONES DESTACADAS
        # --------------------------------------------------
        destacadas = self.publicaciones_destacadas()
        texto.append("")
        texto.append("PUBLICACIONES DESTACADAS")
        texto.append("")

        # ==================================================
        # TOP 5
        # ==================================================
        texto.append("TOP 5 PUBLICACIONES POR IMPRESIONES")
        for posicion, publicacion in enumerate(destacadas["Top 5"], start=1):
            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 0)} | "
                f"Engagement: {publicacion.get('Engagement', 0)}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # ==================================================
        # BOTTOM 5
        # ==================================================
        texto.append("")
        texto.append("BOTTOM 5 PUBLICACIONES POR IMPRESIONES")
        for posicion, publicacion in enumerate(destacadas["Bottom 5"], start=1):
            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 0)} | "
                f"Engagement: {publicacion.get('Engagement', 0)}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        # ==================================================
        # TOP 5 POR ENGAGEMENT
        # ==================================================
        texto.append("")
        texto.append("TOP 5 PUBLICACIONES POR ENGAGEMENT")
        texto.append("")
        for posicion, publicacion in enumerate(destacadas["Top 5 Engagement"], start=1):
            texto.append(
                f"{posicion}. "
                f"Fecha: {publicacion.get('Fecha', 'N/D')} | "
                f"Impresiones: {publicacion.get('Impresiones', 0)} | "
                f"Interacciones: {publicacion.get('Interacciones', 0)} | "
                f"Engagement: {publicacion.get('Engagement', 0)}% | "
                f"URL: {publicacion.get('URL', 'N/D')}"
            )

        return "\n".join(texto)

    # ======================================================
    # CONTEXTO ESTRATÉGICO DEL USUARIO (Método independiente)
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

        texto_contexto.append(f"Sector objetivo: {sector if sector else 'N/D'}")
        texto_contexto.append(f"Intereses profesionales: {intereses if intereses else 'N/D'}")
        texto_contexto.append(f"Objetivo profesional: {objetivo if objetivo else 'N/D'}")
        texto_contexto.append(f"Fecha de activación estratégica: {fecha_activacion if fecha_activacion else 'N/D'}")

        texto_contexto.append("")
        texto_contexto.append(
            "Este contexto debe utilizarse posteriormente para "
            "delimitar la investigación web y evaluar la relevancia "
            "del contenido respecto al campo profesional declarado."
        )

        return "\n".join(texto_contexto)


